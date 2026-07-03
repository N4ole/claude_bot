"""Commande owner `shutdown` : éteint proprement le bot."""
from discord.ext import commands

from utils import checks
from utils.i18n import t


class Shutdown(commands.Cog):
    """Extinction du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="shutdown",
        description="Éteint le bot.",
    )
    @checks.is_owner()
    async def shutdown(self, ctx: commands.Context) -> None:
        await ctx.send(t(ctx, "shutdown.msg"))
        await self.bot.close()

    @shutdown.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shutdown(bot))
