"""Commandes owner `banserv` / `unbanserv` / `banservs` : blacklist de serveurs.

Un serveur blacklisté est quitté immédiatement s'il est présent, et le bot
refuse d'y rester s'il y est réinvité (listener `on_guild_join`). Le
propriétaire du serveur reçoit un MP l'informant du blacklist (avec le lien du
serveur de support), et les owners du bot sont prévenus.
"""
import logging

import discord
from discord.ext import commands

import config
from utils import checks, embeds, storage
from utils.i18n import t

log = logging.getLogger("action")


class BanServ(commands.Cog):
    """Blacklist de serveurs (owners uniquement)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Application du blacklist (départ + MP proprio + alerte owners)
    # ------------------------------------------------------------------ #
    async def _dm_guild_owner(self, guild: discord.Guild) -> bool:
        """Prévient le propriétaire du serveur blacklisté. Renvoie True si envoyé."""
        try:
            owner = guild.owner or await self.bot.fetch_user(guild.owner_id)
        except (discord.HTTPException, discord.NotFound):
            return False
        embed = discord.Embed(
            title=t(guild, "banserv.dm_title"),
            description=t(guild, "banserv.dm_desc", server=guild.name),
            color=discord.Color.red(),
        )
        if config.SUPPORT_SERVER:
            embed.add_field(
                name=t(guild, "banserv.dm_support"),
                value=config.SUPPORT_SERVER, inline=False,
            )
        try:
            await owner.send(embed=embed)
            return True
        except (discord.HTTPException, discord.Forbidden):
            return False

    async def _notify_owners(self, guild: discord.Guild, *, on_join: bool) -> None:
        """Alerte les owners du bot qu'un serveur blacklisté a été quitté."""
        embed = discord.Embed(
            title=t(None, "banserv.alert_title"),
            description=t(None, "banserv.alert_join" if on_join
                          else "banserv.alert_manual"),
            color=discord.Color.dark_red(),
        )
        embed.add_field(name=t(None, "gn.name"), value=guild.name, inline=True)
        embed.add_field(name=t(None, "f.id"), value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name=t(None, "f.owner"),
            value=f"{guild.owner} (`{guild.owner_id}`)" if guild.owner
            else f"`{guild.owner_id}`",
            inline=False,
        )
        for owner_id in checks.all_owner_ids():
            try:
                user = self.bot.get_user(owner_id) or (
                    await self.bot.fetch_user(owner_id)
                )
                await user.send(embed=embed)
            except (discord.HTTPException, discord.NotFound):
                log.warning("Alerte blacklist non délivrée à l'owner %s", owner_id)

    async def _enforce(self, guild: discord.Guild, *, on_join: bool) -> None:
        """Quitte un serveur blacklisté : MP au proprio + alerte owners."""
        await self._dm_guild_owner(guild)
        await self._notify_owners(guild, on_join=on_join)
        try:
            await guild.leave()
        except discord.HTTPException:
            log.warning("Échec du départ du serveur blacklisté %s", guild.id)

    # ------------------------------------------------------------------ #
    # Listener : refus d'un serveur blacklisté à l'invitation
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        if storage.is_blacklisted_guild(guild.id):
            log.info("Serveur blacklisté %s (%s) rejoint puis quitté",
                     guild.name, guild.id)
            await self._enforce(guild, on_join=True)

    # ------------------------------------------------------------------ #
    # Commandes
    # ------------------------------------------------------------------ #
    @commands.command(
        name="banserv",
        description="Blackliste un serveur (le bot le quitte et le refuse).",
    )
    @checks.is_owner()
    async def banserv(self, ctx: commands.Context, guild_id: str) -> None:
        if not guild_id.isdigit():
            await ctx.send(embed=embeds.error(t(ctx, "banserv.bad_id")))
            return
        gid = int(guild_id)
        if not storage.add_blacklisted_guild(gid):
            await ctx.send(embed=embeds.warn(t(ctx, "banserv.already", id=gid)))
            return
        await ctx.send(embed=embeds.success(t(ctx, "banserv.added", id=gid)))
        # Si le bot est actuellement sur ce serveur, on l'applique tout de suite.
        guild = self.bot.get_guild(gid)
        if guild is not None:
            await self._enforce(guild, on_join=False)
            await ctx.send(embed=embeds.info(
                t(ctx, "banserv.left", name=guild.name)))

    @commands.command(
        name="unbanserv",
        description="Retire un serveur de la blacklist.",
    )
    @checks.is_owner()
    async def unbanserv(self, ctx: commands.Context, guild_id: str) -> None:
        if not guild_id.isdigit():
            await ctx.send(embed=embeds.error(t(ctx, "banserv.bad_id")))
            return
        if storage.remove_blacklisted_guild(int(guild_id)):
            await ctx.send(embed=embeds.success(
                t(ctx, "banserv.removed", id=guild_id)))
        else:
            await ctx.send(embed=embeds.warn(
                t(ctx, "banserv.not_listed", id=guild_id)))

    @commands.command(
        name="banservs",
        description="Liste les serveurs blacklistés.",
    )
    @checks.is_owner()
    async def banservs(self, ctx: commands.Context) -> None:
        listed = storage.get_blacklisted_guilds()
        if not listed:
            await ctx.send(embed=embeds.info(t(ctx, "banserv.list_empty")))
            return
        lines = "\n".join(f"• `{gid}`" for gid in listed)
        await ctx.send(embed=embeds.info(
            t(ctx, "banserv.list", count=len(listed), ids=lines)))

    @banserv.error
    @unbanserv.error
    @banservs.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=embeds.error(t(ctx, "error.owner_only")))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=embeds.error(t(ctx, "banserv.usage")))
        else:
            await ctx.send(embed=embeds.error(t(ctx, "error.generic")))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BanServ(bot))
