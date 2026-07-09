"""Commande `remindme <message> <temps>` : rappel en message privé."""
import asyncio
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import replies, storage
from utils.duration import human, parse_duration
from utils.i18n import t


class RemindMe(commands.Cog):
    """Rappels personnels envoyés en message privé."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._resumed = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Reprend les rappels persistés au démarrage (une seule fois)."""
        if self._resumed:
            return
        self._resumed = True
        for reminder in storage.get_reminders():
            self.bot.loop.create_task(self._schedule(reminder))

    async def _schedule(self, reminder: dict) -> None:
        delay = reminder["due"] - datetime.now(timezone.utc).timestamp()
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        await self._fire(reminder)

    async def _fire(self, reminder: dict) -> None:
        user = self.bot.get_user(reminder["user_id"]) or None
        channel = self.bot.get_channel(reminder["channel_id"])
        source = getattr(channel, "guild", None)
        sent = None
        if user is not None:
            sent = await replies.reply_dm(
                user, source, "remind.fire", kind="info",
                message=reminder["message"],
            )
        # Repli sur le salon d'origine (avec ping) si le MP échoue.
        if sent is None and channel is not None:
            try:
                await channel.send(
                    f"<@{reminder['user_id']}> "
                    + t(source, "remind.fire", message=reminder["message"])
                )
            except discord.HTTPException:
                pass
        storage.remove_reminder(reminder["id"])

    @commands.hybrid_command(
        name="remindme",
        description="Te rappelle un message en MP après un délai (ex: 1h30m).",
    )
    async def remindme(
        self, ctx: commands.Context, message: str, temps: str
    ) -> None:
        delta = parse_duration(temps)
        if delta is None:
            await replies.reply(ctx, "remind.bad_duration", kind="error")
            return

        due = datetime.now(timezone.utc) + delta
        reminder = storage.add_reminder(
            ctx.author.id, ctx.channel.id, message, due.timestamp()
        )
        self.bot.loop.create_task(self._schedule(reminder))
        await replies.reply(
            ctx, "remind.set", kind="success", duration=human(delta),
            when=discord.utils.format_dt(due, style="R"),
        )

    @remindme.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await replies.reply(ctx, "remind.usage", kind="error")
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await replies.reply(ctx, "error.generic", kind="error")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemindMe(bot))
