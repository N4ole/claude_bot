"""Constructeurs d'embeds au style uniforme (couleurs, pied de page).

Centralise l'apparence des réponses du bot : une palette cohérente selon le
type de message (succès / erreur / info / avertissement / fun) et un pied de
page commun (nom + version). Les cogs appellent ces fonctions plutôt que de
construire un `discord.Embed` à la main pour un rendu homogène.
"""
import discord

import config

# Palette cohérente (proche des couleurs Discord).
COLOR_SUCCESS = discord.Color.from_rgb(87, 242, 135)
COLOR_ERROR = discord.Color.from_rgb(237, 66, 69)
COLOR_INFO = discord.Color.blurple()
COLOR_WARN = discord.Color.from_rgb(254, 231, 92)
COLOR_FUN = discord.Color.gold()


def _footer(embed: discord.Embed) -> discord.Embed:
    suffix = f"v{config.VERSION}" + (" bêta" if config.BETA else "")
    embed.set_footer(text=f"Watcher · {suffix}")
    return embed


def base(
    description: str | None = None, *, title: str | None = None,
    color: discord.Color = COLOR_INFO,
) -> discord.Embed:
    """Embed de base au style Watcher (couleur + pied de page communs)."""
    return _footer(
        discord.Embed(title=title, description=description, color=color)
    )


def success(description: str, *, title: str | None = None) -> discord.Embed:
    return base(description, title=title, color=COLOR_SUCCESS)


def error(description: str, *, title: str | None = None) -> discord.Embed:
    return base(description, title=title, color=COLOR_ERROR)


def info(description: str, *, title: str | None = None) -> discord.Embed:
    return base(description, title=title, color=COLOR_INFO)


def warn(description: str, *, title: str | None = None) -> discord.Embed:
    return base(description, title=title, color=COLOR_WARN)


def fun(description: str | None = None, *, title: str | None = None) -> discord.Embed:
    return base(description, title=title, color=COLOR_FUN)
