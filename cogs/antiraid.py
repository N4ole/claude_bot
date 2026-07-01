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
from discord.ext import commands

from utils import storage

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
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            await self._ensure_setup(ctx.guild)
            storage.set_setting(ctx.guild.id, "antiraid", True)
            await ctx.send(
                "🛡️ **Anti-raid activé** : les nouveaux membres devront "
                f"valider un captcha dans #{CHANNEL_NAME} pour accéder au serveur."
            )
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antiraid", False)
            await ctx.send(
                "🛡️ **Anti-raid désactivé** : plus de captcha à l'arrivée."
            )
        else:
            await ctx.send("❌ Utilise `antiraid on` ou `antiraid off`.")

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
        await channel.send(
            f"👋 Bienvenue {member.mention} ! Pour accéder au serveur, "
            f"recopie ce code : **`{code}`**\n"
            f"(tu as {CAPTCHA_TIMEOUT // 60} minutes et {MAX_ATTEMPTS} essais)."
        )

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
                    await channel.send(f"✅ {member.mention} vérifié, bienvenue !")
                except discord.HTTPException:
                    pass
                return
            await channel.send(
                f"❌ {member.mention} code incorrect, réessaie."
            )

        # Échec ou expiration : expulsion.
        try:
            await member.kick(reason="Captcha anti-raid non validé")
            await channel.send(f"⛔ {member} n'a pas validé le captcha à temps.")
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiRaid(bot))
