"""Commande admin `antipub on/off` : supprime les invitations Discord."""
import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, storage
from utils.i18n import t

log = logging.getLogger("action")

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}

# Détecte les liens d'invitation Discord (officiels et raccourcis courants).
_INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:discord(?:app)?\.com/invite|discord\.gg|discord\.me|discord\.io|"
    r"dsc\.gg|invite\.gg)/[A-Za-z0-9\-]+",
    re.IGNORECASE,
)


class AntiPub(commands.Cog):
    """Supprime les messages contenant une invitation Discord (si activé)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="antipub",
        description="Active/désactive la suppression des invitations Discord (on/off).",
    )
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def antipub(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, "antipub", True)
            await ctx.send(t(ctx, "antipub.on"))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antipub", False)
            await ctx.send(t(ctx, "antipub.off"))
        else:
            await ctx.send(t(ctx, "toggle.usage", name="antipub"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        # On ne sanctionne pas les administrateurs.
        if checks.is_admin(message.author):
            return
        if not storage.get_setting(message.guild.id, "antipub", False):
            return
        if not _INVITE_RE.search(message.content):
            return

        try:
            await message.delete()
        except discord.HTTPException:
            pass
        await message.channel.send(
            t(message, "antipub.warn", user=message.author.mention),
            delete_after=10,
        )
        log.info(
            "Anti-pub — invitation supprimée de %s (%s) dans #%s / %s (%s)",
            message.author, message.author.id, message.channel,
            message.guild.name, message.guild.id,
        )

    @commands.Cog.listener()
    async def on_message_edit(
        self, _before: discord.Message, after: discord.Message
    ) -> None:
        # Un message édité pour y glisser une invitation est aussi traité.
        await self.on_message(after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiPub(bot))
