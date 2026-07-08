"""Catégories de commandes, partagées par le help et le système de logs.

Chaque commande appartient à une catégorie (clé i18n `cat.*`), déterminée
par le nom de son cog. Les « types de logs » reprennent exactement ces
catégories.
"""
from discord.ext import commands

# Catégorie (clé i18n) et permission (clé i18n ou None), par nom de cog.
CATEGORIES: dict[str, tuple[str, str | None]] = {
    # Infos
    "UserInfo": ("cat.info", None),
    "Avatar": ("cat.info", None),
    "ServerInfo": ("cat.info", None),
    "BotInfo": ("cat.info", None),
    "MemberCount": ("cat.info", None),
    # Utilitaire
    "Poll": ("cat.util", None),
    "Roll": ("cat.util", None),
    "CoinFlip": ("cat.util", None),
    "EightBall": ("cat.util", None),
    "Choose": ("cat.util", None),
    "RemindMe": ("cat.util", None),
    # Modération
    "Watch": ("cat.mod", "dperm.administrator"),
    "Confine": ("cat.mod", "dperm.administrator"),
    "Kick": ("cat.mod", "dperm.kick_members"),
    "Ban": ("cat.mod", "dperm.ban_members"),
    "Mute": ("cat.mod", "dperm.administrator"),
    "VoiceMute": ("cat.mod", "dperm.mute_members"),
    "VoiceDeafen": ("cat.mod", "dperm.deafen_members"),
    "Move": ("cat.mod", "dperm.move_members"),
    "Warn": ("cat.mod", "dperm.administrator"),
    "Note": ("cat.mod", "dperm.administrator"),
    "Clear": ("cat.mod", "dperm.manage_messages"),
    "AntiBot": ("cat.mod", "dperm.administrator"),
    "AntiRaid": ("cat.mod", "dperm.administrator"),
    "AntiPub": ("cat.mod", "dperm.administrator"),
    "AntiSpam": ("cat.mod", "dperm.administrator"),
    "AntiInsulte": ("cat.mod", "dperm.administrator"),
    "Protections": ("cat.mod", "dperm.administrator"),
    "UserStatus": ("cat.mod", "dperm.administrator"),
    "Analyse": ("cat.mod", "dperm.administrator"),
    "Langue": ("cat.mod", "dperm.administrator"),
    "Logs": ("cat.mod", "dperm.administrator"),
    # Propriétaire de serveur
    "ContactOwner": ("cat.owner_server", "perm.server_owner"),
    "Export": ("cat.owner_server", "perm.server_owner"),
    "Prefixe": ("cat.owner_server", "perm.server_owner"),
}
DEFAULT: tuple[str, str | None] = ("cat.general", None)
ORDER = [
    "cat.general", "cat.info", "cat.util", "cat.mod", "cat.owner_server",
]

# Type de log (jeton utilisé par la commande `logs`) <-> clé de catégorie.
TYPE_TO_CAT = {
    "general": "cat.general",
    "info": "cat.info",
    "util": "cat.util",
    "mod": "cat.mod",
    "owner": "cat.owner_server",
}
CAT_TO_TYPE = {cat: token for token, cat in TYPE_TO_CAT.items()}

# Alias acceptés en argument de la commande `logs` (fr/en, variantes).
TYPE_ALIASES = {
    "general": "general", "général": "general", "gen": "general",
    "info": "info", "infos": "info",
    "util": "util", "utilitaire": "util", "utility": "util", "utils": "util",
    "mod": "mod", "moderation": "mod", "modération": "mod", "moderación": "mod",
    "owner": "owner", "server": "owner", "serveur": "owner",
    "propriétaire": "owner", "proprio": "owner",
}


def category_of(command: commands.Command) -> tuple[str, str | None]:
    """Renvoie (clé catégorie, clé permission) d'une commande."""
    cog_name = command.cog.qualified_name if command.cog else ""
    return CATEGORIES.get(cog_name, DEFAULT)


def resolve_type(token: str) -> str | None:
    """Normalise un argument de type de log en jeton canonique, ou None."""
    return TYPE_ALIASES.get(token.lower().strip())
