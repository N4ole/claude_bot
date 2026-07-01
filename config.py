"""Chargement de la configuration depuis les variables d'environnement."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

# Token du bot (obligatoire).
TOKEN = os.getenv("DISCORD_TOKEN")

# Préfixe des commandes texte. "§" par défaut.
PREFIX = os.getenv("COMMAND_PREFIX", "§")

# ID du serveur de dev pour la synchro instantanée des commandes slash.
_guild_id = os.getenv("GUILD_ID")
GUILD_ID = int(_guild_id) if _guild_id and _guild_id.isdigit() else None

# ID de l'owner principal du bot (ne peut pas être retiré via rmowner).
_owner_id = os.getenv("OWNER_ID")
OWNER_ID = int(_owner_id) if _owner_id and _owner_id.isdigit() else None

# Version du bot.
VERSION = "1.0.0"

# --- Panel web (OAuth2 Discord) ------------------------------------------- #
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8080/callback"
)
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
# Secret de signature des sessions (généré si absent : sessions non
# persistantes entre deux redémarrages).
WEB_SECRET = os.getenv("WEB_SECRET") or secrets.token_hex(32)

# Le panel n'est démarré que si l'OAuth est configuré.
WEB_ENABLED = bool(OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET)
