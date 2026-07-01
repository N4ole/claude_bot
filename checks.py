"""Vérifications (checks) réutilisables pour les commandes."""
from discord.ext import commands

import config
import storage


def is_owner_id(user_id: int) -> bool:
    """True si l'utilisateur est l'owner principal ou un owner additionnel."""
    if config.OWNER_ID is not None and user_id == config.OWNER_ID:
        return True
    return user_id in storage.get_owners()


def is_owner():
    """Check de commande : réservé aux owners du bot."""

    async def predicate(ctx: commands.Context) -> bool:
        if is_owner_id(ctx.author.id):
            return True
        raise commands.CheckFailure(
            "Cette commande est réservée aux owners du bot."
        )

    return commands.check(predicate)
