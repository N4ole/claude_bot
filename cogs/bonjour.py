"""Commande bonjour : salue l'utilisateur."""
from discord.ext import commands

from utils import embeds
from utils.i18n import t


class Bonjour(commands.Cog):
    """Salue l'utilisateur qui exécute la commande."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="bonjour",
        description="Le bot vous dit bonjour.",
    )
    async def bonjour(self, ctx: commands.Context) -> None:
        await ctx.send(embed=embeds.success(
            t(ctx, "bonjour", user=ctx.author.mention)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bonjour(bot))
