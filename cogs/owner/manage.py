"""Gestion des owners du bot (réservé aux owners).

L'owner principal est défini via OWNER_ID dans le .env et ne peut pas être
retiré. Les owners additionnels sont gérés via addowner / rmowner et stockés
dans owners.json.
"""
import discord
from discord.ext import commands

from utils import checks
import config
from utils import storage


class Owners(commands.Cog):
    """Commandes de gestion des owners du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="addowner",
        description="Ajoute un owner au bot.",
    )
    @checks.is_owner()
    async def addowner(self, ctx: commands.Context, user: discord.User) -> None:
        if checks.is_owner_id(user.id):
            await ctx.send(f"⚠️ {user.mention} est déjà owner.")
            return

        storage.add_owner(user.id)
        await ctx.send(f"✅ {user.mention} est désormais owner du bot.")

    @commands.hybrid_command(
        name="rmowner",
        description="Retire un owner du bot.",
    )
    @checks.is_owner()
    async def rmowner(self, ctx: commands.Context, user: discord.User) -> None:
        if config.OWNER_ID is not None and user.id == config.OWNER_ID:
            await ctx.send("⛔ L'owner principal ne peut pas être retiré.")
            return

        if storage.remove_owner(user.id):
            await ctx.send(f"✅ {user.mention} n'est plus owner du bot.")
        else:
            await ctx.send(f"⚠️ {user.mention} n'était pas owner.")

    @commands.hybrid_command(
        name="owners",
        description="Liste les owners du bot.",
    )
    @checks.is_owner()
    async def owners(self, ctx: commands.Context) -> None:
        lines = []
        if config.OWNER_ID is not None:
            lines.append(f"• <@{config.OWNER_ID}> (principal)")
        for owner_id in storage.get_owners():
            lines.append(f"• <@{owner_id}>")

        embed = discord.Embed(
            title="👑 Owners du bot",
            description="\n".join(lines) or "Aucun owner défini.",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @addowner.error
    @rmowner.error
    @owners.error
    async def _owner_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        elif isinstance(error, (commands.UserNotFound, commands.BadArgument)):
            await ctx.send("❌ Utilisateur introuvable.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Owners(bot))
