"""Commande admin `clear` : supprime un nombre de messages du salon."""
import discord
from discord.ext import commands

from utils import checks

from utils.i18n import t

MAX_CLEAR = 100


class Clear(commands.Cog):
    """Nettoyage de messages (réservé aux modérateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        description="Supprime un nombre de messages du salon (max 100).",
    )
    @checks.manage_messages()
    async def clear(self, ctx: commands.Context, nombre: int) -> None:
        if nombre < 1:
            await ctx.send(t(ctx, "clear.bad_number"))
            return
        nombre = min(nombre, MAX_CLEAR)

        # En préfixe, on retire aussi le message de commande.
        if ctx.interaction is None:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass

        deleted = await ctx.channel.purge(limit=nombre)
        await ctx.send(
            t(ctx, "clear.done", count=len(deleted)),
            delete_after=5,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
