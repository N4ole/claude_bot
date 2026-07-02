"""Commande owner `say` : fait parler le bot."""
import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t


class Say(commands.Cog):
    """Fait envoyer un message par le bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="say",
        description="Fait parler le bot dans le salon courant.",
    )
    @checks.is_owner()
    async def say(self, ctx: commands.Context, *, message: str) -> None:
        # Envoie le message dans le salon.
        await ctx.channel.send(message)

        # Nettoyage / accusé de réception selon le type d'invocation.
        if ctx.interaction is not None:
            await ctx.interaction.response.send_message(
                t(ctx, "say.sent"), ephemeral=True
            )
        elif ctx.message is not None:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass

    @say.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(t(ctx, "say.missing"))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Say(bot))
