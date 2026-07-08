"""Commande `prefixe` : choix du préfixe du bot, par serveur.

Réservée au **propriétaire du serveur**. Le choix est persisté dans
`data/guild_settings.json` (clé `prefix`) et survit aux redémarrages ; le
`.env` ne porte que le préfixe **par défaut** (`!`). Sans argument, affiche
le préfixe actuel. La mention du bot reste toujours utilisable comme
préfixe de secours.
"""
import logging

from discord.ext import commands

import config
from utils import checks, embeds, storage
from utils.i18n import t

log = logging.getLogger("action")

# Garde-fous : court, sans espace, et pas un déclencheur naturel de Discord.
MAX_LEN = 5
_FORBIDDEN = {"@", "#", "/"}


class Prefixe(commands.Cog):
    """Préfixe personnalisé par serveur (propriétaire du serveur)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="prefixe",
        description="Affiche ou change le préfixe du bot sur ce serveur.",
    )
    @checks.server_owner()
    async def prefixe(
        self, ctx: commands.Context, nouveau: str | None = None
    ) -> None:
        current = storage.get_prefix(ctx.guild.id)

        # Sans argument : afficher le préfixe actuel.
        if nouveau is None:
            await ctx.send(embed=embeds.info(
                t(ctx, "prefix.current", prefix=current,
                  default=config.PREFIX)))
            return

        nouveau = nouveau.strip()
        if (not nouveau or len(nouveau) > MAX_LEN or " " in nouveau
                or nouveau in _FORBIDDEN):
            await ctx.send(embed=embeds.error(
                t(ctx, "prefix.invalid", max=MAX_LEN)))
            return

        # `reset`/`default` : retour au préfixe par défaut.
        if nouveau.lower() in {"reset", "default", "defaut", "défaut"}:
            storage.set_setting(ctx.guild.id, "prefix", None)
            log.info(
                "Préfixe réinitialisé (%s) sur %s (%s) par %s",
                config.PREFIX, ctx.guild.name, ctx.guild.id, ctx.author,
            )
            await ctx.send(embed=embeds.success(
                t(ctx, "prefix.reset", prefix=config.PREFIX)))
            return

        storage.set_setting(ctx.guild.id, "prefix", nouveau)
        log.info(
            "Préfixe changé en '%s' sur %s (%s) par %s",
            nouveau, ctx.guild.name, ctx.guild.id, ctx.author,
        )
        await ctx.send(embed=embeds.success(
            t(ctx, "prefix.set", prefix=nouveau)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Prefixe(bot))
