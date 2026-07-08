"""Rotation du statut Discord du bot (« joue à … » / « regarde … »).

Fait défiler périodiquement plusieurs statuts :
  - `!help, v0.20 bêta`      (aide + version)
  - `1.2k utilisateurs`      (total des membres, abrégé : 1k pour 1000)
  - `8 serveurs`             (nombre de serveurs)
  - `42 commandes`           (nombre de commandes du bot)

Le statut est global (un seul pour tout le bot) : il n'est donc pas traduit
par serveur et reste en français (langue par défaut du bot).
"""
import logging

import discord
from discord.ext import commands, tasks

import config

log = logging.getLogger(__name__)

# Intervalle entre deux statuts (secondes). Assez espacé pour rester sous les
# limites de débit des mises à jour de présence de la passerelle Discord.
ROTATE_SECONDS = 20


def _compact(n: int) -> str:
    """Abrège un nombre : 1000 -> 1k, 1500 -> 1.5k, 2_000_000 -> 2M.

    Tronque au dixième (pas d'arrondi) pour éviter des artefacts du type
    « 1000k » sur 999 999.
    """
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        value = int(n / 100) / 10  # tronque à une décimale
        return f"{value:.1f}".rstrip("0").rstrip(".") + "k"
    value = int(n / 100_000) / 10
    return f"{value:.1f}".rstrip("0").rstrip(".") + "M"


class Presence(commands.Cog):
    """Fait défiler le statut du bot en boucle."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._index = 0
        self.rotate.start()

    async def cog_unload(self) -> None:
        self.rotate.cancel()

    def _version_label(self) -> str:
        return f"v{config.VERSION} bêta" if config.BETA else f"v{config.VERSION}"

    def _statuses(self) -> list[tuple[discord.ActivityType, str]]:
        """Liste (type d'activité, texte) des statuts à faire défiler."""
        members = sum(g.member_count or 0 for g in self.bot.guilds)
        servers = len(self.bot.guilds)
        commands_count = len(self.bot.commands)
        return [
            (discord.ActivityType.playing,
             f"{config.PREFIX}help, {self._version_label()}"),
            (discord.ActivityType.watching,
             f"{_compact(members)} utilisateurs"),
            (discord.ActivityType.watching,
             f"{_compact(servers)} serveurs"),
            (discord.ActivityType.playing,
             f"{_compact(commands_count)} commandes"),
        ]

    @tasks.loop(seconds=ROTATE_SECONDS)
    async def rotate(self) -> None:
        statuses = self._statuses()
        activity_type, text = statuses[self._index % len(statuses)]
        self._index += 1
        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=activity_type, name=text)
            )
        except discord.HTTPException:
            log.warning("Échec de la mise à jour du statut (%s)", text)

    @rotate.before_loop
    async def _before(self) -> None:
        # Attend la connexion : member_count et guilds ne sont fiables
        # qu'une fois le bot prêt.
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Presence(bot))
