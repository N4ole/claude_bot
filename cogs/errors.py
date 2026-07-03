"""Gestionnaire d'erreurs global : messages clairs, permissions manquantes.

Note (audit Q1) : plusieurs cogs écoutent `on_command_error`, chacun avec un
rôle distinct et non redondant :
  - `errors`      (ici)          → message utilisateur clair et traduit ;
  - `errorreport` (owners)       → MP détaillé aux owners sur bug inattendu ;
  - `logs`        (salon Discord) → trace l'échec dans le salon de catégorie ;
  - `actionlog`                  → journalise l'échec (fichiers/console).
Les listeners d'un même événement coexistent volontairement.
"""
import logging

from discord.ext import commands

import config
from utils.i18n import t

log = logging.getLogger(__name__)


def _perms(source, perms: list[str]) -> str:
    """Traduit une liste de permissions Discord via i18n (clés `dperm.*`)."""
    labels = []
    for p in perms:
        key = f"dperm.{p}"
        label = t(source, key)
        labels.append(label if label != key else p.replace("_", " "))
    return ", ".join(labels)


class Errors(commands.Cog):
    """Traite les erreurs de commandes de façon centralisée."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        # On laisse la main aux gestionnaires locaux (@cmd.error) s'ils existent.
        if ctx.command is not None and ctx.command.has_error_handler():
            return
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(t(ctx, "error.missing_perms",
                             perms=_perms(ctx, error.missing_permissions)))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(t(ctx, "error.bot_missing_perms",
                             perms=_perms(ctx, error.missing_permissions)))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(t(ctx, "error.no_dm"))
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(t(ctx, "error.dm_only"))
        elif isinstance(error, commands.CheckFailure):
            message = str(error) or t(ctx, "error.check_failure")
            await ctx.send(f"⛔ {message}" if str(error) else message)
        elif isinstance(error, commands.MissingRequiredArgument):
            usage = (
                f"{config.PREFIX}{ctx.command.qualified_name} "
                f"{ctx.command.signature}"
            )
            await ctx.send(t(ctx, "error.missing_argument", usage=usage))
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await ctx.send(t(ctx, "error.member_not_found"))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(t(ctx, "error.bad_argument", error=error))
        else:
            log.exception(
                "Erreur non gérée dans la commande %s",
                ctx.command, exc_info=error,
            )
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
