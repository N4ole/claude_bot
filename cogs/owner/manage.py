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
from utils.i18n import t


class Owners(commands.Cog):
    """Commandes de gestion des owners du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="addowner",
        description="Ajoute un owner au bot.",
    )
    @checks.is_owner()
    async def addowner(self, ctx: commands.Context, user: discord.User) -> None:
        if checks.is_owner_id(user.id):
            await ctx.send(t(ctx, "own.already", user=user.mention))
            return

        storage.add_owner(user.id)
        await ctx.send(t(ctx, "own.added", user=user.mention))

    @commands.command(
        name="rmowner",
        description="Retire un owner du bot.",
    )
    @checks.is_owner()
    async def rmowner(self, ctx: commands.Context, user: discord.User) -> None:
        if config.OWNER_ID is not None and user.id == config.OWNER_ID:
            await ctx.send(t(ctx, "own.principal_protect"))
            return

        if storage.remove_owner(user.id):
            await ctx.send(t(ctx, "own.removed", user=user.mention))
        else:
            await ctx.send(t(ctx, "own.not_owner", user=user.mention))

    @commands.command(
        name="owners",
        description="Liste les owners du bot.",
    )
    @checks.is_owner()
    async def owners(self, ctx: commands.Context) -> None:
        lines = []
        if config.OWNER_ID is not None:
            lines.append(f"• <@{config.OWNER_ID}> {t(ctx, 'own.principal')}")
        for owner_id in storage.get_owners():
            lines.append(f"• <@{owner_id}>")

        embed = discord.Embed(
            title=t(ctx, "own.list_title"),
            description="\n".join(lines) or t(ctx, "own.list_empty"),
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @addowner.error
    @rmowner.error
    @owners.error
    async def _owner_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        elif isinstance(error, (commands.UserNotFound, commands.BadArgument)):
            await ctx.send(t(ctx, "error.member_not_found"))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Owners(bot))
