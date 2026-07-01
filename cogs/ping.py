"""Commande ping : affiche la latence du bot."""
import discord
from discord.ext import commands


class Ping(commands.Cog):
    """Vérifie que le bot répond et mesure sa latence."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Affiche la latence du bot.")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"Latence : **{latency_ms} ms**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
