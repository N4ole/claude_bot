"""Définition de la classe du bot et chargement automatique des commandes."""
import logging
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

import config

log = logging.getLogger(__name__)

# Dossier contenant un fichier par commande (cog).
COGS_DIR = Path(__file__).parent / "cogs"


class ClaudeBot(commands.Bot):
    """Bot Discord supportant les commandes préfixe (§) et slash (/)."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        # Nécessaire pour lire le contenu des messages (commandes préfixe
        # et copie des messages surveillés).
        intents.message_content = True
        # Nécessaire pour résoudre les membres (commande watch).
        intents.members = True
        # Nécessaire pour suivre les connexions/déconnexions vocales.
        intents.voice_states = True
        # Nécessaire pour suivre les changements de statut (watch).
        intents.presences = True

        # Heure de démarrage du bot (pour la commande uptime).
        self.start_time = datetime.now(timezone.utc)

        super().__init__(
            command_prefix=commands.when_mentioned_or(config.PREFIX),
            intents=intents,
            help_command=None,  # On fournit notre propre commande help.
        )

    async def setup_hook(self) -> None:
        """Charge les cogs et synchronise les commandes slash au démarrage."""
        await self._load_cogs()
        await self._sync_commands()

    async def _load_cogs(self) -> None:
        """Charge chaque fichier .py de cogs/ et de ses sous-dossiers."""
        for file in sorted(COGS_DIR.rglob("*.py")):
            if file.stem.startswith("_"):
                continue
            # Transforme le chemin en module pointé, ex :
            #   cogs/ping.py         -> cogs.ping
            #   cogs/owner/reload.py -> cogs.owner.reload
            relative = file.relative_to(COGS_DIR.parent).with_suffix("")
            extension = ".".join(relative.parts)
            try:
                await self.load_extension(extension)
                log.info("Cog chargé : %s", extension)
            except Exception:  # noqa: BLE001
                log.exception("Échec du chargement du cog : %s", extension)

    async def _sync_commands(self) -> None:
        """Synchronise l'arbre des commandes slash avec Discord."""
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("%d commandes slash synchronisées sur le serveur %s",
                     len(synced), config.GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("%d commandes slash synchronisées globalement", len(synced))

    async def on_ready(self) -> None:
        log.info("Connecté en tant que %s (id: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Game(name=f"{config.PREFIX}help")
        )
