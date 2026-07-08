"""Commande owner `leave <id>` : fait quitter un serveur au bot."""
import logging

import discord
from discord.ext import commands

from utils import checks, embeds
from utils.i18n import t

log = logging.getLogger("action")


class Leave(commands.Cog):
    """Fait quitter un serveur au bot (owners uniquement)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="leave",
        description="Fait quitter un serveur au bot (par ID).",
    )
    @checks.is_owner()
    async def leave(self, ctx: commands.Context, guild_id: str) -> None:
        if not guild_id.isdigit():
            await ctx.send(embed=embeds.error(t(ctx, "leave.bad_id")))
            return
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            await ctx.send(embed=embeds.error(t(ctx, "leave.not_found")))
            return
        name = guild.name
        try:
            await guild.leave()
        except discord.HTTPException as exc:
            await ctx.send(embed=embeds.error(t(ctx, "leave.failed", error=exc)))
            return
        log.info("Bot retiré du serveur %s (%s) par %s", name, guild_id,
                 ctx.author)
        await ctx.send(embed=embeds.success(
            t(ctx, "leave.done", name=name, id=guild_id)))

    @leave.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=embeds.error(t(ctx, "error.owner_only")))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=embeds.error(t(ctx, "leave.usage")))
        else:
            await ctx.send(embed=embeds.error(t(ctx, "error.generic")))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leave(bot))
