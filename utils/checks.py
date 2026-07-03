"""Vérifications (checks) réutilisables pour les commandes."""
from discord.ext import commands

import config
from utils import storage


class OwnerOnly(commands.CheckFailure):
    """Levée quand une commande réservée aux owners est refusée.

    Type dédié (plutôt qu'un message dans l'exception) : le gestionnaire
    d'erreurs global affiche un message i18n selon le type, sans jamais
    relayer le texte brut d'une exception.
    """


def is_owner_id(user_id: int) -> bool:
    """True si l'utilisateur est l'owner principal ou un owner additionnel."""
    if config.OWNER_ID is not None and user_id == config.OWNER_ID:
        return True
    return user_id in storage.get_owners()


def all_owner_ids() -> list[int]:
    """Liste des IDs de tous les owners (principal en tête, puis additionnels)."""
    ids = list(storage.get_owners())
    if config.OWNER_ID is not None and config.OWNER_ID not in ids:
        ids.insert(0, config.OWNER_ID)
    return ids


def is_owner():
    """Check de commande : réservé aux owners du bot."""

    async def predicate(ctx: commands.Context) -> bool:
        if is_owner_id(ctx.author.id):
            return True
        raise OwnerOnly()

    return commands.check(predicate)
