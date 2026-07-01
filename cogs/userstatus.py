"""Commande admin `userstatus` : historique des sanctions d'un utilisateur."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import storage

_LABELS = {
    "warn": "⚠️ Avertissements",
    "mute": "🔇 Mutes",
    "unmute": "🔊 Unmutes",
    "confine": "🔒 Confinements",
}


def _fmt_duration(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


class UserStatus(commands.Cog):
    """Récapitulatif des actions de modération reçues par un utilisateur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userstatus",
        description="Affiche l'historique des sanctions d'un utilisateur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def userstatus(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        actions = storage.get_modlog(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=f"📋 Dossier de {member}",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # État actuel.
        warns = storage.get_warns(ctx.guild.id, member.id)
        etats = [f"Avertissements actuels : **{warns}/5**"]
        if member.timed_out_until is not None and (
            member.timed_out_until > datetime.now(timezone.utc)
        ):
            etats.append(
                "🔇 Actuellement mute jusqu'à "
                + discord.utils.format_dt(member.timed_out_until, style="R")
            )
        confined = any(
            uid == member.id
            for gid, uid, _ in storage.get_confinements()
            if gid == ctx.guild.id
        )
        if confined:
            etats.append("🔒 Actuellement confiné")
        embed.add_field(name="État actuel", value="\n".join(etats), inline=False)

        # Compteurs par type + durée totale de mute.
        counts: dict[str, int] = {}
        total_mute = 0.0
        for a in actions:
            counts[a["type"]] = counts.get(a["type"], 0) + 1
            if a["type"] == "mute" and a.get("duration"):
                total_mute += a["duration"]

        if counts:
            summary = "\n".join(
                f"{_LABELS.get(t, t)} : **{n}**"
                for t, n in sorted(counts.items())
            )
            if total_mute:
                summary += f"\n⏱️ Temps de mute cumulé : **{_fmt_duration(total_mute)}**"
            embed.add_field(name="Total", value=summary, inline=False)
        else:
            embed.add_field(
                name="Total", value="Aucune sanction enregistrée.", inline=False
            )

        # Détail des dernières actions (10 max).
        if actions:
            lines = []
            for a in actions[-10:]:
                ts = discord.utils.format_dt(
                    datetime.fromtimestamp(a["ts"], tz=timezone.utc), style="f"
                )
                label = _LABELS.get(a["type"], a["type"]).split(" ", 1)[-1]
                extra = f" — {a['detail']}" if a.get("detail") else ""
                if a.get("duration"):
                    extra += f" ({_fmt_duration(a['duration'])})"
                mod = f" par <@{a['moderator']}>" if a.get("moderator") else ""
                lines.append(f"• {ts} — {label}{extra}{mod}")
            embed.add_field(
                name="Dernières actions", value="\n".join(lines), inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserStatus(bot))
