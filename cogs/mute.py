"""Commandes admin `mute` / `unmute` : coupe la parole via le timeout Discord.

La durée accepte un format court, combinable :
    30s, 5m, 2h, 1d, ou une combinaison comme "1h30m".
Le timeout Discord est limité à 28 jours maximum.
"""
from datetime import timedelta

import discord
from discord.ext import commands

from utils import checks, replies, storage
from utils.duration import parse_duration

# Durée maximale d'un timeout Discord.
MAX_TIMEOUT = timedelta(days=28)


class Mute(commands.Cog):
    """Mute temporisé d'utilisateurs (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mute",
        description="Coupe la parole à un utilisateur pour une durée (ex: 5m, 1h30m).",
    )
    @checks.admin()
    async def mute(
        self, ctx: commands.Context, member: discord.Member, duree: str
    ) -> None:
        delta = parse_duration(duree)
        if delta is None:
            await replies.reply(ctx, "mute.bad_duration", kind="error")
            return
        if delta > MAX_TIMEOUT:
            await replies.reply(ctx, "mute.too_long", kind="error")
            return

        try:
            await member.timeout(delta, reason=f"Mute par {ctx.author}")
        except discord.Forbidden:
            await replies.reply(ctx, "mute.forbidden", kind="error")
            return
        except discord.HTTPException as exc:
            await replies.reply(ctx, "mute.failed", kind="error", error=str(exc))
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "mute", ctx.author.id,
            duration=delta.total_seconds(), detail=duree,
        )

        until = discord.utils.utcnow() + delta
        spec = (
            replies.Embed("warn", color=discord.Color.orange())
            .title("mute.title")
            .desc("mute.done", user=member.mention)
            .field("mute.until", discord.utils.format_dt(until, style="F"))
            .field("mute.relative", discord.utils.format_dt(until, style="R"))
        )
        await replies.reply_rich(ctx, spec)

    @commands.hybrid_command(
        name="unmute",
        description="Rend la parole à un utilisateur mute.",
    )
    @checks.admin()
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        if member.timed_out_until is None:
            await replies.reply(ctx, "unmute.not_muted", kind="warn",
                                user=member.mention)
            return

        try:
            await member.timeout(None, reason=f"Unmute par {ctx.author}")
        except discord.HTTPException as exc:
            await replies.reply(ctx, "unmute.failed", kind="error",
                                error=str(exc))
            return

        storage.add_modlog(ctx.guild.id, member.id, "unmute", ctx.author.id)
        await replies.reply(ctx, "unmute.done", kind="success",
                            user=member.mention)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mute(bot))
