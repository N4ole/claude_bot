"""Commandes admin `mute` / `unmute` : coupe la parole via le timeout Discord.

La durée accepte un format court, combinable :
    30s, 5m, 2h, 1d, ou une combinaison comme "1h30m".
Le timeout Discord est limité à 28 jours maximum.
"""
import re
from datetime import timedelta

import discord
from discord.ext import commands

from utils import storage

# Durée maximale d'un timeout Discord.
MAX_TIMEOUT = timedelta(days=28)

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "j": 86400}
_DURATION_RE = re.compile(r"(\d+)\s*([smhdj])", re.IGNORECASE)


def parse_duration(text: str) -> timedelta | None:
    """Convertit '1h30m' / '5m' / '30s' en timedelta. None si invalide."""
    matches = _DURATION_RE.findall(text)
    if not matches:
        return None
    total = sum(int(value) * _UNITS[unit.lower()] for value, unit in matches)
    if total <= 0:
        return None
    return timedelta(seconds=total)


class Mute(commands.Cog):
    """Mute temporisé d'utilisateurs (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mute",
        description="Coupe la parole à un utilisateur pour une durée (ex: 5m, 1h30m).",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mute(
        self, ctx: commands.Context, member: discord.Member, duree: str
    ) -> None:
        delta = parse_duration(duree)
        if delta is None:
            await ctx.send(
                "❌ Durée invalide. Exemples : `30s`, `5m`, `2h`, `1d`, `1h30m`."
            )
            return
        if delta > MAX_TIMEOUT:
            await ctx.send("❌ La durée maximale d'un mute est de 28 jours.")
            return

        try:
            await member.timeout(delta, reason=f"Mute par {ctx.author}")
        except discord.Forbidden:
            await ctx.send(
                "⛔ Impossible de mute ce membre (permissions ou hiérarchie)."
            )
            return
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Échec du mute : {exc}")
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "mute", ctx.author.id,
            duration=delta.total_seconds(), detail=duree,
        )

        until = discord.utils.utcnow() + delta
        embed = discord.Embed(
            title="🔇 Mute",
            description=f"{member.mention} est mute.",
            color=discord.Color.orange(),
        )
        embed.add_field(
            name="Jusqu'à",
            value=discord.utils.format_dt(until, style="F"),
            inline=True,
        )
        embed.add_field(
            name="Soit", value=discord.utils.format_dt(until, style="R"), inline=True
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="unmute",
        description="Rend la parole à un utilisateur mute.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        if member.timed_out_until is None:
            await ctx.send(f"{member.mention} n'est pas mute.")
            return

        try:
            await member.timeout(None, reason=f"Unmute par {ctx.author}")
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Échec du unmute : {exc}")
            return

        storage.add_modlog(ctx.guild.id, member.id, "unmute", ctx.author.id)
        await ctx.send(f"🔊 {member.mention} n'est plus mute.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mute(bot))
