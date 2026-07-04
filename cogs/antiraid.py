"""Commande admin `antiraid on/off` : captcha à l'arrivée des nouveaux membres.

Quand l'anti-raid est activé, chaque nouveau membre reçoit un rôle
« Non vérifié » qui masque le serveur, et doit recopier un code (captcha
simple, sans API externe) dans le salon de vérification pour y accéder.
"""
import asyncio
import logging
import random
import string

import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, storage
from utils.i18n import t

log = logging.getLogger(__name__)

ROLE_NAME = "Non vérifié"
CHANNEL_NAME = "vérification"
CAPTCHA_TIMEOUT = 300  # secondes
MAX_ATTEMPTS = 3

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}


def _new_code(length: int = 6) -> str:
    # Sans caractères ambigus (0/O, 1/I).
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(alphabet, k=length))


class AntiRaid(commands.Cog):
    """Vérification par captcha des nouveaux membres (si activé)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _ensure_setup(
        self, guild: discord.Guild
    ) -> tuple[discord.Role, discord.TextChannel]:
        """Crée/récupère le rôle « Non vérifié » et le salon de vérification."""
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if role is None:
            role = await guild.create_role(
                name=ROLE_NAME,
                permissions=discord.Permissions.none(),
                reason="Anti-raid",
            )

        # Le rôle « Non vérifié » ne voit aucune catégorie...
        deny = discord.PermissionOverwrite(view_channel=False)
        for category in guild.categories:
            if category.overwrites_for(role).is_empty():
                try:
                    await category.set_permissions(role, overwrite=deny)
                except discord.HTTPException:
                    pass

        # ...sauf le salon de vérification.
        channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                role: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    read_message_history=True,
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                ),
            }
            channel = await guild.create_text_channel(
                CHANNEL_NAME, overwrites=overwrites,
                reason="Anti-raid",
            )
        return role, channel

    @commands.hybrid_command(
        name="antiraid",
        description="Active/désactive le captcha à l'arrivée (on/off).",
    )
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def antiraid(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            await self._ensure_setup(ctx.guild)
            storage.set_setting(ctx.guild.id, "antiraid", True)
            await ctx.send(t(ctx, "antiraid.on", channel=CHANNEL_NAME))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antiraid", False)
            await ctx.send(t(ctx, "antiraid.off"))
        else:
            await ctx.send(t(ctx, "toggle.usage", name="antiraid"))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        if not storage.get_setting(member.guild.id, "antiraid", False):
            return

        guild = member.guild
        role, channel = await self._ensure_setup(guild)
        try:
            await member.add_roles(role, reason="Anti-raid : en attente de captcha")
        except discord.HTTPException:
            return

        code = _new_code()
        await channel.send(t(
            guild, "antiraid.welcome", user=member.mention, code=code,
            minutes=CAPTCHA_TIMEOUT // 60, attempts=MAX_ATTEMPTS,
        ))

        def check(msg: discord.Message) -> bool:
            return msg.author == member and msg.channel == channel

        for _ in range(MAX_ATTEMPTS):
            try:
                msg = await self.bot.wait_for(
                    "message", check=check, timeout=CAPTCHA_TIMEOUT
                )
            except asyncio.TimeoutError:
                break
            if msg.content.strip().upper() == code:
                try:
                    await member.remove_roles(role, reason="Captcha validé")
                    await channel.send(
                        t(guild, "antiraid.verified", user=member.mention)
                    )
                    log.info(
                        "Anti-raid — %s (%s) a validé le captcha sur %s (%s)",
                        member, member.id, guild.name, guild.id,
                    )
                except discord.HTTPException:
                    pass
                return
            await channel.send(
                t(guild, "antiraid.wrong", user=member.mention)
            )

        # Échec ou expiration : expulsion.
        try:
            await member.kick(reason="Captcha anti-raid non validé")
            await channel.send(t(guild, "antiraid.kicked", user=str(member)))
            log.info(
                "Anti-raid — %s (%s) expulsé (captcha non validé) sur %s (%s)",
                member, member.id, guild.name, guild.id,
            )
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiRaid(bot))
