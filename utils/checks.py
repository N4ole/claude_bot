"""Vérifications de permissions : SOURCE UNIQUE pour tout le bot.

Toute vérification de permission (décorateur de commande ou prédicat
utilisé dans un listener) vit ici. Les cogs ne réécrivent JAMAIS de logique
de permission : ils appellent une fonction de ce module.

Décorateurs de commandes :
    @checks.admin()            serveur uniquement + Administrateur
    @checks.kick_perms()       serveur + Expulser (utilisateur ET bot)
    @checks.ban_perms()        serveur + Bannir (utilisateur ET bot)
    @checks.manage_messages()  serveur + Gérer les messages
    @checks.mute_voice_perms() serveur + Rendre muet des membres (vocal)
    @checks.deafen_voice_perms() serveur + Rendre sourd des membres (vocal)
    @checks.move_perms()       serveur + Déplacer des membres (vocal)
    @checks.server_owner()     serveur + propriétaire du serveur Discord
    @checks.is_owner()         owners du bot (préfixe/MP inclus)

Prédicats (listeners, logique interne) :
    checks.is_admin(member)               exemption automod, etc.
    checks.can_act_on(author, target)     hiérarchie des rôles (kick/ban)
    checks.is_owner_or_server_owner(ctx)  export, fonctions partagées
    checks.is_owner_id(user_id)           owners du bot (web, listeners)
"""
from discord.ext import commands

import config
from utils import storage


class OwnerOnly(commands.CheckFailure):
    """Levée quand une commande réservée aux owners est refusée.

    Type dédié (plutôt qu'un message dans l'exception) : le gestionnaire
    d'erreurs global affiche un message i18n selon le type, sans jamais
    relayer le texte brut d'une exception.
    """


class ServerOwnerOnly(commands.CheckFailure):
    """Levée quand une commande réservée au propriétaire du serveur est
    refusée. Affichée en i18n par le gestionnaire global (`co.not_owner`)."""


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


# --------------------------------------------------------------------------- #
# Décorateurs de commandes (empilent les checks discord.py standard)
# --------------------------------------------------------------------------- #
def _compose(*decorators):
    """Combine plusieurs décorateurs discord.py en un seul."""

    def deco(func):
        for d in reversed(decorators):
            func = d(func)
        return func

    return deco


def admin():
    """Serveur uniquement + permission Administrateur."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(administrator=True),
    )


def kick_perms():
    """Serveur + « Expulser des membres » (pour l'utilisateur ET le bot)."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(kick_members=True),
        commands.bot_has_permissions(kick_members=True),
    )


def ban_perms():
    """Serveur + « Bannir des membres » (pour l'utilisateur ET le bot)."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(ban_members=True),
        commands.bot_has_permissions(ban_members=True),
    )


def manage_messages():
    """Serveur uniquement + permission « Gérer les messages »."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(manage_messages=True),
    )


def mute_voice_perms():
    """Serveur + « Rendre muet des membres » (utilisateur ET bot)."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(mute_members=True),
        commands.bot_has_permissions(mute_members=True),
    )


def deafen_voice_perms():
    """Serveur + « Rendre sourd des membres » (utilisateur ET bot)."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(deafen_members=True),
        commands.bot_has_permissions(deafen_members=True),
    )


def move_perms():
    """Serveur + « Déplacer des membres » vocalement (utilisateur ET bot)."""
    return _compose(
        commands.guild_only(),
        commands.has_permissions(move_members=True),
        commands.bot_has_permissions(move_members=True),
    )


def server_owner():
    """Serveur uniquement + réservé au propriétaire du serveur Discord."""

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is not None and ctx.author.id == ctx.guild.owner_id:
            return True
        raise ServerOwnerOnly()

    return _compose(commands.guild_only(), commands.check(predicate))


# --------------------------------------------------------------------------- #
# Prédicats (listeners et logique interne — pas des checks de commande)
# --------------------------------------------------------------------------- #
def is_admin(member) -> bool:
    """True si le membre est administrateur du serveur (exemption automod)."""
    perms = getattr(member, "guild_permissions", None)
    return bool(perms and perms.administrator)


def can_act_on(author, target) -> bool:
    """True si `author` peut sanctionner `target` (hiérarchie des rôles).

    Le propriétaire du serveur outrepasse toujours ; sinon le rôle le plus
    haut de l'auteur doit être STRICTEMENT au-dessus de celui de la cible.
    """
    if author.guild is not None and author.id == author.guild.owner_id:
        return True
    return target.top_role < author.top_role


def is_owner_or_server_owner(ctx: commands.Context) -> bool:
    """True si l'auteur est owner du bot OU propriétaire du serveur."""
    if is_owner_id(ctx.author.id):
        return True
    return ctx.guild is not None and ctx.author.id == ctx.guild.owner_id
