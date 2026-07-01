"""Anti full-majuscules : supprime et sanctionne les messages en majuscules."""
import discord
from discord.ext import commands

from utils import automod


class AntiCaps(commands.Cog):
    """Modération automatique des messages en majuscules (>75%)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # (guild_id, user_id) -> nombre d'infractions.
        self._counts: dict[tuple[int, int], int] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        # On ne sanctionne pas les administrateurs.
        if message.author.guild_permissions.administrator:
            return
        if not automod.is_caps_spam(message.content):
            return

        key = (message.guild.id, message.author.id)
        self._counts[key] = self._counts.get(key, 0) + 1
        await automod.apply_escalation(
            message, self._counts[key], "Anti-majuscules"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiCaps(bot))
