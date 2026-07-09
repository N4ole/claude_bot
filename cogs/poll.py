"""Commande `poll` : crée un sondage à réactions (oui/non ou choix multiples)."""
import discord
from discord.ext import commands

from utils import replies
from utils.i18n import t

_NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class Poll(commands.Cog):
    """Sondages par réactions."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="poll",
        description="Crée un sondage. Options séparées par des « | » (facultatif).",
    )
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, *, question: str) -> None:
        # Options optionnelles séparées par « | ».
        parts = [p.strip() for p in question.split("|")]
        titre = parts[0]
        options = [p for p in parts[1:] if p]

        if len(options) > 10:
            await replies.reply(ctx, "poll.too_many", kind="error")
            return

        embed = discord.Embed(
            title=t(ctx, "poll.title"),
            description=titre,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=t(ctx, "poll.by", user=ctx.author))

        if options:
            embed.description += "\n\n" + "\n".join(
                f"{_NUMBER_EMOJIS[i]} {opt}" for i, opt in enumerate(options)
            )
            emojis = _NUMBER_EMOJIS[: len(options)]
        else:
            emojis = ["✅", "❌"]

        message = await ctx.send(embed=embed)
        for emoji in emojis:
            await message.add_reaction(emoji)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot))
