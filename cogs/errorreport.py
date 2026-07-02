"""Envoie un MP détaillé aux owners du bot lors d'une erreur inattendue.

Deux sources d'erreurs sont surveillées :

* les **erreurs de commande** non prévues (bug réel dans une commande), en
  ignorant les erreurs « normales » déjà gérées ailleurs (permissions
  manquantes, mauvais arguments, cooldown, commande introuvable…) ;
* les **erreurs d'événements** (listeners) remontées globalement via
  ``on_error``.

Chaque owner reçoit un embed résumant le type, le message, le contexte
(commande/événement, auteur, salon, serveur, horodatage) et la trace
complète (jointe en fichier ``.txt`` si elle est trop longue).
"""
import io
import logging
import sys
import time
import traceback
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks

log = logging.getLogger("action")

# Erreurs « attendues » (côté utilisateur) : déjà signalées à l'utilisateur
# et/ou journalisées, elles ne constituent pas un bug à remonter aux owners.
_IGNORED = (
    commands.CommandNotFound,
    commands.CheckFailure,       # is_owner, has_permissions, guild_only…
    commands.UserInputError,     # BadArgument, MissingRequiredArgument…
    commands.CommandOnCooldown,
    commands.MaxConcurrencyReached,
    commands.DisabledCommand,
)

# Anti-spam : une même signature d'erreur n'est renvoyée qu'une fois par
# fenêtre (en secondes), pour éviter de noyer les owners.
_DEDUP_WINDOW = 300
# Limite avant de basculer la trace dans un fichier joint plutôt qu'un champ.
_INLINE_TB_LIMIT = 1000


class ErrorReport(commands.Cog):
    """Notifie les owners du bot des erreurs inattendues, en MP."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # signature -> dernier envoi (time.monotonic).
        self._recent: dict[str, float] = {}
        # Garde-fou contre une récursion (une erreur pendant l'envoi d'un MP
        # ne doit pas déclencher un nouvel envoi à l'infini).
        self._reporting = False

    def _should_dedup(self, signature: str) -> bool:
        now = time.monotonic()
        # Purge des entrées expirées.
        for key, ts in list(self._recent.items()):
            if now - ts > _DEDUP_WINDOW:
                del self._recent[key]
        if signature in self._recent:
            return True
        self._recent[signature] = now
        return False

    @staticmethod
    def _format_tb(error: BaseException) -> str:
        return "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    async def _dispatch(
        self, title: str, fields: list[tuple[str, str]], tb_text: str,
        signature: str,
    ) -> None:
        """Construit et envoie le rapport à tous les owners (avec anti-spam)."""
        if self._should_dedup(signature):
            log.debug("Erreur déjà signalée récemment, MP ignoré : %s", signature)
            return

        embed = discord.Embed(
            title=title,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        for name, value in fields:
            # Sécurité : un champ d'embed est limité à 1024 caractères.
            embed.add_field(name=name, value=value[:1024] or "—", inline=False)

        file = None
        if len(tb_text) <= _INLINE_TB_LIMIT:
            embed.add_field(
                name="Traceback", value=f"```py\n{tb_text[:1000]}\n```",
                inline=False,
            )
        else:
            # Trace trop longue : on la joint en fichier.
            file = discord.File(
                io.BytesIO(tb_text.encode("utf-8")), filename="traceback.txt"
            )
            embed.add_field(
                name="Traceback",
                value="Trace complète jointe (`traceback.txt`).",
                inline=False,
            )
        embed.set_footer(text="ClaudeBot — rapport d'erreur automatique")

        self._reporting = True
        try:
            for owner_id in checks.all_owner_ids():
                try:
                    user = self.bot.get_user(owner_id) or (
                        await self.bot.fetch_user(owner_id)
                    )
                    # discord.File est à usage unique : on le recrée par envoi.
                    kwargs = {"embed": embed}
                    if file is not None:
                        kwargs["file"] = discord.File(
                            io.BytesIO(tb_text.encode("utf-8")),
                            filename="traceback.txt",
                        )
                    await user.send(**kwargs)
                except (discord.HTTPException, discord.NotFound):
                    log.warning(
                        "Impossible d'envoyer le rapport d'erreur à l'owner %s",
                        owner_id,
                    )
        finally:
            self._reporting = False

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        # On ne remonte que les bugs réels, pas les erreurs utilisateur.
        if isinstance(error, _IGNORED):
            return
        # On déballe l'exception d'origine (CommandInvokeError, HybridError…).
        original = getattr(error, "original", error)

        where = "MP"
        if ctx.guild is not None:
            channel = getattr(ctx.channel, "name", "?")
            where = f"#{channel} — {ctx.guild.name} ({ctx.guild.id})"
        cmd = ctx.command.qualified_name if ctx.command else "?"

        fields = [
            ("Type", f"`{type(original).__name__}`"),
            ("Message", str(original) or "—"),
            ("Commande", f"`{cmd}`"),
            ("Auteur", f"{ctx.author} (`{ctx.author.id}`)"),
            ("Où", where),
        ]
        signature = f"cmd:{cmd}:{type(original).__name__}:{original}"
        await self._dispatch(
            "⚠️ Erreur de commande", fields, self._format_tb(original),
            signature,
        )
        log.error(
            "Erreur commande /%s par %s (%s) : %s",
            cmd, ctx.author, ctx.author.id, type(original).__name__,
        )

    async def report_event_error(self, event: str) -> None:
        """Signale une erreur d'événement (appelée par ClaudeBot.on_error).

        Les erreurs d'événements ne sont pas dispatchées aux listeners de cog :
        ``ClaudeBot.on_error`` délègue donc ici. L'exception courante est lue
        via ``sys.exc_info()`` (toujours valide dans le bloc ``except``).
        """
        # Évite toute récursion si l'erreur survient pendant notre envoi de MP.
        if self._reporting:
            return
        exc_type, exc, exc_tb = sys.exc_info()
        if exc is None:
            return
        tb_text = "".join(traceback.format_exception(exc_type, exc, exc_tb))
        fields = [
            ("Type", f"`{type(exc).__name__}`"),
            ("Message", str(exc) or "—"),
            ("Événement", f"`{event}`"),
        ]
        signature = f"event:{event}:{type(exc).__name__}:{exc}"
        await self._dispatch(
            "⚠️ Erreur d'événement", fields, tb_text, signature
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ErrorReport(bot))
