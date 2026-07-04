"""Commande admin `antispam on/off` : sanctionne les envois trop rapides."""
import logging
import time
from collections import defaultdict, deque
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, storage
from utils.i18n import t

log = logging.getLogger("action")

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}

# Seuil : plus de MAX_MESSAGES messages en WINDOW secondes = spam.
MAX_MESSAGES = 5
WINDOW = 5.0
# Durée du mute (timeout) appliqué en cas de spam.
MUTE_DURATION = timedelta(minutes=1)


class AntiSpam(commands.Cog):
    """Détecte et sanctionne le spam de messages (si activé)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # (guild_id, user_id) -> horodatages récents.
        self._history: dict[tuple[int, int], deque] = defaultdict(
            lambda: deque(maxlen=MAX_MESSAGES)
        )

    @commands.hybrid_command(
        name="antispam",
        description="Active/désactive l'anti-spam (on/off).",
    )
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def antispam(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, "antispam", True)
            await ctx.send(t(
                ctx, "antispam.on", max=MAX_MESSAGES, window=int(WINDOW),
                minutes=int(MUTE_DURATION.total_seconds() // 60),
            ))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antispam", False)
            await ctx.send(t(ctx, "antispam.off"))
        else:
            await ctx.send(t(ctx, "toggle.usage", name="antispam"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if checks.is_admin(message.author):
            return
        if not storage.get_setting(message.guild.id, "antispam", False):
            return

        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        history = self._history[key]
        history.append(now)

        # Nombre de messages dans la fenêtre glissante.
        recent = [ts for ts in history if now - ts <= WINDOW]
        if len(recent) < MAX_MESSAGES:
            return

        # Spam détecté : on réinitialise, on mute et on prévient.
        history.clear()
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        try:
            await message.author.timeout(MUTE_DURATION, reason="Anti-spam")
            storage.add_modlog(
                message.guild.id, message.author.id, "mute",
                self.bot.user.id if self.bot.user else None,
                duration=MUTE_DURATION.total_seconds(), detail="anti-spam",
            )
        except discord.HTTPException:
            pass
        await message.channel.send(
            t(message, "antispam.warn", user=message.author.mention,
              minutes=int(MUTE_DURATION.total_seconds() // 60)),
            delete_after=10,
        )
        log.info(
            "Anti-spam — %s (%s) mute %d min dans #%s / %s (%s)",
            message.author, message.author.id,
            int(MUTE_DURATION.total_seconds() // 60), message.channel,
            message.guild.name, message.guild.id,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiSpam(bot))
