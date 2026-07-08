"""Commande `8ball` : boule magique qui répond à une question (embed)."""
import random

import discord
from discord.ext import commands

from utils import embeds
from utils.i18n import EIGHTBALL, get_lang, t


class EightBall(commands.Cog):
    """La boule magique."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Pose une question à la boule magique.",
    )
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        answers = EIGHTBALL.get(get_lang(ctx), EIGHTBALL["fr"])
        embed = embeds.fun(f"🎱 {random.choice(answers)}",
                           title=t(ctx, "8ball.title"))
        embed.add_field(name=t(ctx, "8ball.question"),
                        value=question[:1024], inline=False)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EightBall(bot))
