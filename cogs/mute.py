"""Commandes admin `mute` / `unmute` : coupe la parole via le timeout Discord.

La durée accepte un format court, combinable :
    30s, 5m, 2h, 1d, ou une combinaison comme "1h30m".
Le timeout Discord est limité à 28 jours maximum.
"""
from datetime import timedelta

import discord
from discord.ext import commands

from utils import checks, storage
from utils.duration import parse_duration
from utils.i18n import t

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
            await ctx.send(t(ctx, "mute.bad_duration"))
            return
        if delta > MAX_TIMEOUT:
            await ctx.send(t(ctx, "mute.too_long"))
            return

        try:
            await member.timeout(delta, reason=f"Mute par {ctx.author}")
        except discord.Forbidden:
            await ctx.send(t(ctx, "mute.forbidden"))
            return
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "mute.failed", error=exc))
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "mute", ctx.author.id,
            duration=delta.total_seconds(), detail=duree,
        )

        until = discord.utils.utcnow() + delta
        embed = discord.Embed(
            title=t(ctx, "mute.title"),
            description=t(ctx, "mute.done", user=member.mention),
            color=discord.Color.orange(),
        )
        embed.add_field(
            name=t(ctx, "mute.until"),
            value=discord.utils.format_dt(until, style="F"),
            inline=True,
        )
        embed.add_field(
            name=t(ctx, "mute.relative"),
            value=discord.utils.format_dt(until, style="R"), inline=True,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="unmute",
        description="Rend la parole à un utilisateur mute.",
    )
    @checks.admin()
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        if member.timed_out_until is None:
            await ctx.send(t(ctx, "unmute.not_muted", user=member.mention))
            return

        try:
            await member.timeout(None, reason=f"Unmute par {ctx.author}")
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "unmute.failed", error=exc))
            return

        storage.add_modlog(ctx.guild.id, member.id, "unmute", ctx.author.id)
        await ctx.send(t(ctx, "unmute.done", user=member.mention))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mute(bot))
