"""Chargement de la configuration depuis les variables d'environnement."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

# Token du bot (obligatoire).
TOKEN = os.getenv("DISCORD_TOKEN")

# Préfixe PAR DÉFAUT des commandes texte ("!"). Chaque propriétaire de
# serveur peut le personnaliser via la commande `prefixe` (persisté dans
# data/guild_settings.json — voir storage.get_prefix).
PREFIX = os.getenv("COMMAND_PREFIX", "!")

# ID du serveur de dev pour la synchro instantanée des commandes slash.
_guild_id = os.getenv("GUILD_ID")
GUILD_ID = int(_guild_id) if _guild_id and _guild_id.isdigit() else None

# ID de l'owner principal du bot (ne peut pas être retiré via rmowner).
_owner_id = os.getenv("OWNER_ID")
OWNER_ID = int(_owner_id) if _owner_id and _owner_id.isdigit() else None

# Version du bot. Le bot est actuellement en bêta.
VERSION = "0.20"
BETA = True

# URL du dépôt GitHub (liens de PR dans les notifications de mise à jour).
REPO_URL = os.getenv("REPO_URL", "https://github.com/N4ole/Watcher")

# Invitation vers le serveur de support (mentionnée dans le MP envoyé au
# propriétaire d'un serveur blacklisté). Vide = aucun lien affiché.
SUPPORT_SERVER = os.getenv("SUPPORT_SERVER", "")

# --- Panel web (OAuth2 Discord) ------------------------------------------- #
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://localhost:8080/callback"
)
# Écoute en local par défaut : exposition publique volontaire via WEB_HOST
# (par ex. 0.0.0.0 derrière un reverse-proxy HTTPS).
WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
# Secret de signature des sessions (généré si absent : sessions non
# persistantes entre deux redémarrages).
WEB_SECRET = os.getenv("WEB_SECRET") or secrets.token_hex(32)

# Le panel n'est démarré que si l'OAuth est configuré.
WEB_ENABLED = bool(OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET)
