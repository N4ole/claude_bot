"""Commande admin `userstatus` : historique des sanctions d'un utilisateur."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks, storage
from utils.i18n import t

_LABEL_KEYS = {
    "warn": "us.warns_label",
    "mute": "us.mute_label",
    "unmute": "us.unmute_label",
    "kick": "us.kick_label",
    "ban": "us.ban_label",
    "unban": "us.unban_label",
    "confine": "us.confine_label",
    "unconfine": "us.unconfine_label",
    "vmute": "us.vmute_label",
    "vunmute": "us.vunmute_label",
    "vdeafen": "us.vdeafen_label",
    "vundeafen": "us.vundeafen_label",
    "move": "us.move_label",
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

    def _label(self, ctx, action_type: str) -> str:
        key = _LABEL_KEYS.get(action_type)
        return t(ctx, key) if key else action_type

    @commands.hybrid_command(
        name="userstatus",
        description="Affiche l'historique des sanctions d'un utilisateur.",
    )
    @checks.admin()
    async def userstatus(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        actions = storage.get_modlog(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=t(ctx, "us.title", user=member),
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # État actuel.
        warns = storage.get_warns(ctx.guild.id, member.id)
        etats = [t(ctx, "us.warns_now", count=warns)]
        if member.timed_out_until is not None and (
            member.timed_out_until > datetime.now(timezone.utc)
        ):
            etats.append(
                t(ctx, "us.muted_until")
                + discord.utils.format_dt(member.timed_out_until, style="R")
            )
        confined = any(
            uid == member.id
            for gid, uid, _ in storage.get_confinements()
            if gid == ctx.guild.id
        )
        if confined:
            etats.append(t(ctx, "us.confined_now"))
        embed.add_field(
            name=t(ctx, "us.current"), value="\n".join(etats), inline=False
        )

        # Compteurs par type + durée totale de mute.
        counts: dict[str, int] = {}
        total_mute = 0.0
        for action in actions:
            counts[action["type"]] = counts.get(action["type"], 0) + 1
            if action["type"] == "mute" and action.get("duration"):
                total_mute += action["duration"]

        if counts:
            summary = "\n".join(
                f"{self._label(ctx, typ)} : **{n}**"
                for typ, n in sorted(counts.items())
            )
            if total_mute:
                summary += "\n" + t(ctx, "us.mute_time",
                                    duration=_fmt_duration(total_mute))
            embed.add_field(name=t(ctx, "us.total"), value=summary, inline=False)
        else:
            embed.add_field(
                name=t(ctx, "us.total"), value=t(ctx, "us.no_sanction"),
                inline=False,
            )

        # Détail des dernières actions (10 max).
        if actions:
            lines = []
            for action in actions[-10:]:
                ts = discord.utils.format_dt(
                    datetime.fromtimestamp(action["ts"], tz=timezone.utc),
                    style="f",
                )
                label = self._label(ctx, action["type"]).split(" ", 1)[-1]
                extra = f" — {action['detail']}" if action.get("detail") else ""
                if action.get("duration"):
                    extra += f" ({_fmt_duration(action['duration'])})"
                mod = (
                    f" {t(ctx, 'us.by')} <@{action['moderator']}>"
                    if action.get("moderator") else ""
                )
                lines.append(f"• {ts} — {label}{extra}{mod}")
            embed.add_field(
                name=t(ctx, "us.recent"), value="\n".join(lines), inline=False
            )

        # Notes de dossier (libres, ajoutées via la commande `note`).
        notes = storage.get_notes(ctx.guild.id, member.id)
        if notes:
            note_lines = []
            for i, note in enumerate(notes, start=1):
                ts = discord.utils.format_dt(
                    datetime.fromtimestamp(note["ts"], tz=timezone.utc),
                    style="d",
                )
                mod = (
                    f" — <@{note['moderator']}>" if note.get("moderator") else ""
                )
                note_lines.append(f"**{i}.** {note['text']} ({ts}{mod})")
            # L'embed limite un champ à 1024 caractères : on tronque au besoin.
            value = "\n".join(note_lines)
            if len(value) > 1024:
                value = value[:1013] + "\n…"
            embed.add_field(name=t(ctx, "us.notes"), value=value, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserStatus(bot))
