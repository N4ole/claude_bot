"""Commande owner `shutdown` : éteint proprement le bot."""
from discord.ext import commands

import checks


class Shutdown(commands.Cog):
    """Extinction du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="shutdown",
        description="Éteint le bot.",
    )
    @checks.is_owner()
    async def shutdown(self, ctx: commands.Context) -> None:
        await ctx.send("🛑 Extinction du bot...")
        await self.bot.close()

    @shutdown.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shutdown(bot))
