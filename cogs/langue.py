"""Commande admin `langue` : choisit la langue du bot (fr/en) pour le serveur."""
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, embeds, storage
from utils.i18n import LANGS, t

_ALIASES = {
    "fr": "fr", "français": "fr", "francais": "fr", "french": "fr",
    "en": "en", "anglais": "en", "english": "en",
}


class Langue(commands.Cog):
    """Choix de la langue du bot (français par défaut)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="langue",
        description="Choisit la langue du bot pour ce serveur (fr/en).",
    )
    @app_commands.choices(langue=appchoices.langs())
    @checks.admin()
    async def langue(
        self, ctx: commands.Context, langue: str | None = None
    ) -> None:
        if langue is None:
            await ctx.send(embed=embeds.info(t(ctx, "lang.current")))
            return

        chosen = _ALIASES.get(langue.lower())
        if chosen not in LANGS:
            await ctx.send(embed=embeds.error(t(ctx, "lang.invalid")))
            return

        storage.set_setting(ctx.guild.id, "lang", chosen)
        # Le message de confirmation est déjà dans la nouvelle langue.
        await ctx.send(embed=embeds.success(t(ctx, "lang.set")))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Langue(bot))
