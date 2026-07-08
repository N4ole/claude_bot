"""Résolution des salons de logs Discord — SOURCE UNIQUE, hors commande `logs`.

Le salon de log d'un serveur pour un « type » (jeton de `categories`, ex.
`mod`) est stocké dans le réglage `logtypes` du serveur : `{token: channel_id}`.
La commande `logs` écrit ce réglage ; ce module ne fait que le lire, pour que
les autres cogs (événements de modération hors commande, anti-bot, etc.)
puissent écrire dans le bon salon sans dupliquer la logique.
"""
import discord

from utils import storage

# Clé du réglage de serveur : {token: channel_id}. Partagée avec le cog `logs`.
SETTING = "logtypes"
# Nom de la catégorie Discord qui regroupe les salons de logs.
CATEGORY_NAME = "logs"


def log_channel(guild: discord.Guild, token: str) -> discord.TextChannel | None:
    """Salon de log d'un serveur pour un type donné, ou None s'il est absent.

    Renvoie None si le type n'est pas activé ou si le salon a été supprimé.
    """
    channel_id = (storage.get_setting(guild.id, SETTING, {}) or {}).get(token)
    if not channel_id:
        return None
    channel = guild.get_channel(channel_id)
    return channel if hasattr(channel, "send") else None
