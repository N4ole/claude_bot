"""Prévient les owners du bot en MP quand Watcher rejoint/quitte un serveur.

Chaque owner reçoit un embed avec les informations du serveur concerné
(nom, ID, propriétaire, membres, date de création) et le nombre total de
serveurs après l'événement.
"""
import logging

import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t

log = logging.getLogger("action")


class GuildNotify(commands.Cog):
    """Notifie les owners du bot des arrivées/départs de serveurs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _guild_embed(self, guild: discord.Guild, *, joined: bool) -> discord.Embed:
        bots = sum(1 for m in guild.members if m.bot)
        humans = (guild.member_count or 0) - bots
        embed = discord.Embed(
            title=t(None, "gn.join_title" if joined else "gn.leave_title"),
            description=guild.description or None,
            color=discord.Color.green() if joined else discord.Color.red(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name=t(None, "gn.name"), value=guild.name, inline=True)
        embed.add_field(name=t(None, "f.id"), value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name=t(None, "f.owner"),
            value=f"{guild.owner} (`{guild.owner_id}`)" if guild.owner
            else f"`{guild.owner_id}`",
            inline=False,
        )
        embed.add_field(
            name=t(None, "f.members"),
            value=t(None, "gn.members_val", count=guild.member_count or 0,
                    humans=humans, bots=bots),
            inline=False,
        )
        if guild.created_at:
            embed.add_field(
                name=t(None, "f.created"),
                value=discord.utils.format_dt(guild.created_at, style="D"),
                inline=True,
            )
        embed.add_field(name=t(None, "gn.total"),
                        value=str(len(self.bot.guilds)), inline=True)
        return embed

    async def _notify_owners(self, embed: discord.Embed) -> None:
        for owner_id in checks.all_owner_ids():
            try:
                user = self.bot.get_user(owner_id) or (
                    await self.bot.fetch_user(owner_id)
                )
                await user.send(embed=embed)
            except (discord.HTTPException, discord.NotFound):
                log.warning(
                    "Notification serveur non délivrée à l'owner %s", owner_id
                )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        # (actionlog journalise déjà l'événement ; ici on prévient les owners.)
        await self._notify_owners(self._guild_embed(guild, joined=True))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self._notify_owners(self._guild_embed(guild, joined=False))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildNotify(bot))
