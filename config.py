"""Chargement de la configuration depuis les variables d'environnement."""
import os

from dotenv import load_dotenv

load_dotenv()

# Token du bot (obligatoire).
TOKEN = os.getenv("DISCORD_TOKEN")

# Préfixe des commandes texte. "§" par défaut.
PREFIX = os.getenv("COMMAND_PREFIX", "§")

# ID du serveur de dev pour la synchro instantanée des commandes slash.
_guild_id = os.getenv("GUILD_ID")
GUILD_ID = int(_guild_id) if _guild_id and _guild_id.isdigit() else None
