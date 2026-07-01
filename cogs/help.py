"""Commande help : liste toutes les commandes disponibles."""
import discord
from discord.ext import commands

import config


class Help(commands.Cog):
    """Affiche la liste des commandes du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="Affiche la liste des commandes disponibles.",
    )
    async def help(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="📖 Aide",
            description=(
                f"Préfixe : `{config.PREFIX}` — les commandes sont aussi "
                "disponibles en slash `/`."
            ),
            color=discord.Color.blurple(),
        )

        # Liste chaque commande enregistrée, hors commandes masquées et
        # hors commandes d'owner (dossier cogs/owner/).
        shown = [
            command
            for command in sorted(self.bot.commands, key=lambda c: c.name)
            if not command.hidden
            and not (command.module and command.module.startswith("cogs.owner"))
        ]
        for command in shown:
            description = command.description or "Pas de description."
            embed.add_field(
                name=f"{config.PREFIX}{command.name}",
                value=description,
                inline=False,
            )

        embed.set_footer(text=f"{len(shown)} commande(s) disponible(s)")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
