"""Attribue un rôle 'owner-claudebot' aux owners qui rejoignent un serveur."""
import logging

import discord
from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)

OWNER_ROLE_NAME = "owner-claudebot"


class OwnerRole(commands.Cog):
    """Gestion du rôle réservé aux owners du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _ensure_role(self, guild: discord.Guild) -> discord.Role | None:
        """Récupère (ou crée) le rôle owner-claudebot, sans permissions."""
        role = discord.utils.get(guild.roles, name=OWNER_ROLE_NAME)
        if role is not None:
            return role
        try:
            return await guild.create_role(
                name=OWNER_ROLE_NAME,
                permissions=discord.Permissions.none(),
                reason="Rôle réservé aux owners du bot",
            )
        except discord.HTTPException:
            log.warning("Impossible de créer le rôle %s sur %s",
                        OWNER_ROLE_NAME, guild.name)
            return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot or not checks.is_owner_id(member.id):
            return

        role = await self._ensure_role(member.guild)
        if role is None:
            return
        try:
            await member.add_roles(role, reason="Owner du bot")
            log.info("Rôle %s attribué à %s sur %s",
                     OWNER_ROLE_NAME, member, member.guild.name)
        except discord.HTTPException:
            log.warning("Impossible d'attribuer %s à %s",
                        OWNER_ROLE_NAME, member)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OwnerRole(bot))
