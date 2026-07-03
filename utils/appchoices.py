"""Listes de choix slash (`app_commands.Choice`) réutilisables.

Ces choix n'affectent QUE l'interface slash : le nom affiché est libre, la
`value` transmise reste celle attendue par le code. En préfixe, les
paramètres restent de simples `str` (souplesse des synonymes conservée).
"""
from discord import app_commands


def onoff() -> list[app_commands.Choice[str]]:
    """Choix « Activer / Désactiver » (valeurs `on` / `off`)."""
    return [
        app_commands.Choice(name="Activer / On", value="on"),
        app_commands.Choice(name="Désactiver / Off", value="off"),
    ]


def langs() -> list[app_commands.Choice[str]]:
    """Choix de langue (valeurs `fr` / `en`)."""
    return [
        app_commands.Choice(name="Français", value="fr"),
        app_commands.Choice(name="English", value="en"),
    ]
