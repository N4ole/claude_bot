"""Anti full-emojis : supprime et sanctionne les messages saturés d'emojis."""
import discord
from discord.ext import commands

import automod


class AntiEmoji(commands.Cog):
    """Modération automatique des messages composés surtout d'emojis (>75%)."""

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
        if not automod.is_emoji_spam(message.content):
            return

        key = (message.guild.id, message.author.id)
        self._counts[key] = self._counts.get(key, 0) + 1
        await automod.apply_escalation(
            message, self._counts[key], "Anti-emojis"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiEmoji(bot))
