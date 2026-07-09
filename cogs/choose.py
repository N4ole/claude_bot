"""Commande `choose` : le bot choisit parmi des options séparées par « | »."""
import random

from discord.ext import commands

from utils import replies


class Choose(commands.Cog):
    """Choix aléatoire parmi plusieurs options."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="choose",
        description="Choisit une option parmi plusieurs (séparées par « | »).",
    )
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            await replies.reply(ctx, "choose.need", kind="error")
            return
        spec = (
            replies.Embed("fun")
            .title("choose.title")
            .desc("choose.result", choice=random.choice(choices))
            .field("choose.options",
                   ", ".join(f"`{c}`" for c in choices)[:1024], inline=False)
        )
        await replies.reply_rich(ctx, spec)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Choose(bot))
