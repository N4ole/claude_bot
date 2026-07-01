"""Cog du panel web : démarre le serveur, échantillonne et enregistre les stats."""
import logging

from aiohttp import web
from discord.ext import commands, tasks

import config
from web import stats
from web import web_app

log = logging.getLogger(__name__)


class WebPanel(commands.Cog):
    """Panel web d'administration (statistiques)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._runner: web.AppRunner | None = None

    async def cog_load(self) -> None:
        if not config.WEB_ENABLED:
            log.info(
                "Panel web désactivé (OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET "
                "manquants)."
            )
            return
        app = web_app.build_app(self.bot)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, config.WEB_HOST, config.WEB_PORT)
        await site.start()
        log.info(
            "Panel web démarré sur http://%s:%d", config.WEB_HOST, config.WEB_PORT
        )
        self._sample_stats.start()

    async def cog_unload(self) -> None:
        self._sample_stats.cancel()
        if self._runner is not None:
            await self._runner.cleanup()

    def _snapshot(self) -> None:
        guilds = [
            (g.id, g.name, g.member_count or 0) for g in self.bot.guilds
        ]
        stats.record_snapshot(guilds)

    @tasks.loop(hours=1)
    async def _sample_stats(self) -> None:
        self._snapshot()

    @_sample_stats.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()
        # Premier instantané dès que le bot est prêt.
        self._snapshot()

    # Enregistre l'utilisation des commandes par serveur.
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        if ctx.guild is not None:
            stats.record_usage(ctx.guild.id)

    # Met à jour l'instantané lors d'un changement de serveur.
    @commands.Cog.listener()
    async def on_guild_join(self, _guild) -> None:
        self._snapshot()

    @commands.Cog.listener()
    async def on_guild_remove(self, _guild) -> None:
        self._snapshot()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WebPanel(bot))
