"""Commande admin `clear` : supprime un nombre de messages du salon."""
import discord
from discord.ext import commands

MAX_CLEAR = 100


class Clear(commands.Cog):
    """Nettoyage de messages (réservé aux modérateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        description="Supprime un nombre de messages du salon (max 100).",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, nombre: int) -> None:
        if nombre < 1:
            await ctx.send("❌ Indique un nombre supérieur à 0.")
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
            f"🧹 {len(deleted)} message(s) supprimé(s).",
            delete_after=5,
            ephemeral=True,
        )

    @clear.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "⛔ Il te faut la permission *Gérer les messages*."
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage : `clear <nombre>`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Le nombre doit être un entier.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
