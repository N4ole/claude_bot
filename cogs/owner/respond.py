"""Commande owner `respond` : répond en MP aux propriétaires de serveurs.

Miroir de `contactowner` : permet aux owners du bot d'envoyer un message
privé à un propriétaire de serveur (pour répondre à un `contactowner`), ou
de diffuser une annonce à tous les propriétaires de serveurs avec `all`.

    respond <ID utilisateur | all> <message>

L'ID d'utilisateur est notamment visible dans la commande `serveurs`
(champ « Propriétaire »).
"""
import logging

import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t

log = logging.getLogger("action")


class Respond(commands.Cog):
    """Répond aux propriétaires de serveurs / diffuse des annonces (owners)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _embed(self, source, message: str, author, *, announce: bool) -> discord.Embed:
        embed = discord.Embed(
            title=t(source, "resp.announce_title" if announce
                    else "resp.dm_title"),
            description=message[:4096],
            color=discord.Color.gold() if announce else discord.Color.blurple(),
        )
        embed.add_field(name=t(source, "resp.from"), value=str(author),
                        inline=False)
        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return embed

    async def _dm(self, user_id: int, embed: discord.Embed) -> bool:
        try:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(
                user_id
            )
            await user.send(embed=embed)
            return True
        except (discord.HTTPException, discord.NotFound):
            return False

    @commands.hybrid_command(
        name="respond",
        description="Répond en MP à un propriétaire de serveur, ou `all` pour une annonce.",
    )
    @checks.is_owner()
    async def respond(
        self, ctx: commands.Context, cible: str, *, message: str
    ) -> None:
        # --- Annonce à tous les propriétaires de serveurs ---
        if cible.lower() == "all":
            # Un seul MP par propriétaire, dans la langue de son serveur.
            owners: dict[int, discord.Guild] = {}
            for guild in self.bot.guilds:
                if guild.owner_id and guild.owner_id not in owners:
                    owners[guild.owner_id] = guild
            if not owners:
                await ctx.send(t(ctx, "resp.no_owners"))
                return

            sent = failed = 0
            for owner_id, guild in owners.items():
                embed = self._embed(guild, message, ctx.author, announce=True)
                if await self._dm(owner_id, embed):
                    sent += 1
                else:
                    failed += 1
            await ctx.send(t(ctx, "resp.announced", sent=sent, failed=failed))
            log.info(
                "Annonce respond envoyée par %s (%s) à %d propriétaire(s), "
                "%d échec(s)",
                ctx.author, ctx.author.id, sent, failed,
            )
            return

        # --- Réponse à un utilisateur précis ---
        if not cible.isdigit():
            await ctx.send(t(ctx, "resp.bad_id", prefix=ctx.prefix or "§"))
            return
        user_id = int(cible)

        # Langue : celle du serveur possédé par la cible si on la connaît.
        source = ctx.guild
        for guild in self.bot.guilds:
            if guild.owner_id == user_id:
                source = guild
                break

        embed = self._embed(source, message, ctx.author, announce=False)
        if await self._dm(user_id, embed):
            user = self.bot.get_user(user_id)
            await ctx.send(t(ctx, "resp.sent_one",
                             user=user or user_id, id=user_id))
            log.info(
                "Réponse respond envoyée par %s (%s) à %s",
                ctx.author, ctx.author.id, user_id,
            )
        else:
            await ctx.send(t(ctx, "resp.fail_one", id=user_id))

    @respond.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(t(ctx, "resp.usage", prefix=ctx.prefix or "§"))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Respond(bot))
