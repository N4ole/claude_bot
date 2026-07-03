"""Commande `status` : version, ping, nombre de serveurs et mode debug."""
import discord
from discord.ext import commands

import config
from utils.i18n import t


class Status(commands.Cog):
    """État général du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="status",
        description="Version, ping et nombre de serveurs.",
    )
    async def status(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title=t(ctx, "st.title"),
            color=discord.Color.blurple(),
        )
        version = t(ctx, "bi.version_val", version=config.VERSION) \
            if config.BETA else config.VERSION
        embed.add_field(name=t(ctx, "bi.version"), value=version, inline=True)
        embed.add_field(
            name=t(ctx, "bi.ping"),
            value=f"{round(self.bot.latency * 1000)} ms", inline=True,
        )
        embed.add_field(
            name=t(ctx, "bi.servers"), value=str(len(self.bot.guilds)), inline=True
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
