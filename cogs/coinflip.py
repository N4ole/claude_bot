"""Commande `coinflip` : pile ou face (embed + bouton « Relancer »)."""
import random

import discord
from discord.ext import commands

from utils import embeds
from utils.i18n import t


def _embed(source) -> discord.Embed:
    result = t(source, random.choice(["coin.heads", "coin.tails"]))
    return embeds.fun(result, title=t(source, "coin.title"))


class RerollView(discord.ui.View):
    """Bouton « Relancer », réservé à l'auteur de la commande."""

    def __init__(self, author_id: int, label: str) -> None:
        super().__init__(timeout=120)
        self.author_id = author_id
        self.reroll.label = label

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                t(interaction.guild, "help.not_for_you"), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary)
    async def reroll(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(
            embed=_embed(interaction.guild), view=self
        )


class CoinFlip(commands.Cog):
    """Pile ou face."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="coinflip",
        aliases=["pileouface"],
        description="Lance une pièce : pile ou face.",
    )
    async def coinflip(self, ctx: commands.Context) -> None:
        view = RerollView(ctx.author.id, t(ctx, "btn.reroll"))
        await ctx.send(embed=_embed(ctx), view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoinFlip(bot))
