"""Commande `roll` : lance des dés au format NdM (ex: 2d6) — embed + relance."""
import random
import re

import discord
from discord.ext import commands

from utils import embeds
from utils.i18n import t

_DICE_RE = re.compile(r"^\s*(\d*)\s*d\s*(\d+)\s*$", re.IGNORECASE)


def _roll_embed(source, des: str, count: int, faces: int) -> discord.Embed:
    rolls = [random.randint(1, faces) for _ in range(count)]
    total = sum(rolls)
    if count > 1:
        detail = " + ".join(map(str, rolls)) + f" = **{total}**"
    else:
        detail = f"**{total}**"
    embed = embeds.fun(title=t(source, "roll.title"))
    embed.add_field(name=f"🎲 {des}", value=detail, inline=False)
    return embed


class RollView(discord.ui.View):
    """Bouton « Relancer » (mêmes dés), réservé à l'auteur."""

    def __init__(self, author_id: int, des: str, count: int, faces: int,
                 label: str) -> None:
        super().__init__(timeout=120)
        self.author_id = author_id
        self.des, self.count, self.faces = des, count, faces
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
        embed = _roll_embed(interaction.guild, self.des, self.count, self.faces)
        await interaction.response.edit_message(embed=embed, view=self)


class Roll(commands.Cog):
    """Lancer de dés."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="roll",
        description="Lance des dés au format NdM (ex: 2d6, d20).",
    )
    async def roll(self, ctx: commands.Context, des: str = "1d6") -> None:
        match = _DICE_RE.match(des)
        if not match:
            await ctx.send(embed=embeds.error(t(ctx, "roll.bad")))
            return

        count = int(match.group(1) or 1)
        faces = int(match.group(2))
        if not (1 <= count <= 100) or not (2 <= faces <= 1000):
            await ctx.send(embed=embeds.error(t(ctx, "roll.limits")))
            return

        # Normalise l'affichage des dés (ex. « d20 » -> « 1d20 »).
        des_label = f"{count}d{faces}"
        view = RollView(ctx.author.id, des_label, count, faces,
                        t(ctx, "btn.reroll"))
        await ctx.send(embed=_roll_embed(ctx, des_label, count, faces),
                       view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roll(bot))
