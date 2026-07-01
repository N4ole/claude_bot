"""Commande `status` : version, ping, nombre de serveurs et mode debug."""
import discord
from discord.ext import commands

import config


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
            title="📊 Statut du bot",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Version", value=config.VERSION, inline=True)
        embed.add_field(
            name="Ping", value=f"{round(self.bot.latency * 1000)} ms", inline=True
        )
        embed.add_field(
            name="Serveurs", value=str(len(self.bot.guilds)), inline=True
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
