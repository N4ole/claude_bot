"""Commande `remindme <message> <temps>` : rappel en message privé."""
import asyncio
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import embeds, storage
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
        text = t(source, "remind.fire", message=reminder["message"])
        sent = False
        if user is not None:
            try:
                await user.send(text)
                sent = True
            except discord.HTTPException:
                sent = False
        # Repli sur le salon d'origine si le MP échoue.
        if not sent and channel is not None:
            try:
                await channel.send(f"<@{reminder['user_id']}> {text}")
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
            await ctx.send(embed=embeds.error(t(ctx, "remind.bad_duration")))
            return

        due = datetime.now(timezone.utc) + delta
        reminder = storage.add_reminder(
            ctx.author.id, ctx.channel.id, message, due.timestamp()
        )
        self.bot.loop.create_task(self._schedule(reminder))
        await ctx.send(embed=embeds.success(
            t(ctx, "remind.set", duration=human(delta),
              when=discord.utils.format_dt(due, style="R"))
        ))

    @remindme.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=embeds.error(t(ctx, "remind.usage")))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemindMe(bot))
