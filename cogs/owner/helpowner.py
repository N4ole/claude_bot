"""Commande owner `helpowner` (préfixe uniquement) : liste les commandes owner."""
import discord
from discord.ext import commands

from utils import checks
import config


class HelpOwner(commands.Cog):
    """Aide dédiée aux commandes d'owner."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="helpowner")
    @checks.is_owner()
    async def helpowner(self, ctx: commands.Context) -> None:
        # Récupère toutes les commandes définies dans le dossier cogs/owner/.
        owner_commands = {
            cmd
            for cmd in self.bot.commands
            if cmd.module and cmd.module.startswith("cogs.owner")
        }

        embed = discord.Embed(
            title="👑 Commandes d'owner",
            description=(
                f"Préfixe : `{config.PREFIX}` — commandes réservées aux owners "
                "du bot."
            ),
            color=discord.Color.gold(),
        )
        for cmd in sorted(owner_commands, key=lambda c: c.name):
            description = cmd.description or cmd.help or "Pas de description."
            embed.add_field(
                name=f"{config.PREFIX}{cmd.name}",
                value=description,
                inline=False,
            )
        embed.set_footer(text=f"{len(owner_commands)} commande(s) d'owner")
        await ctx.send(embed=embed)

    @helpowner.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpOwner(bot))
