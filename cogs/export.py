"""Commande `export` : exporte le journal de modération sur une période.

Réservée aux **owners du bot** et au **propriétaire du serveur**. Génère un
fichier `txt`, `csv` ou `pdf` des actions de modération (kick, ban, mute,
warn, confine…) enregistrées sur la période demandée.

    export <txt|csv|pdf> [période]   (période : ex. 7d, 30d, 12h, ou « all »)
"""
import asyncio
import csv
import io
import logging
import math
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils import checks, storage
from utils.duration import human, parse_duration
from utils.i18n import t

log = logging.getLogger("action")

_FORMATS = ("txt", "csv", "pdf")
_ALL = {"all", "tout", "tous"}
_COLS = ["Date (UTC)", "Utilisateur", "Action", "Modérateur", "Durée", "Détail"]


def _name(guild: discord.Guild, uid) -> str:
    if not uid:
        return "—"
    member = guild.get_member(int(uid))
    return f"{member} ({uid})" if member else str(uid)


def _row(guild: discord.Guild, entry: dict) -> list[str]:
    ts = datetime.fromtimestamp(entry.get("ts", 0), tz=timezone.utc)
    dur = entry.get("duration")
    return [
        ts.strftime("%Y-%m-%d %H:%M"),
        _name(guild, entry.get("user_id")),
        str(entry.get("type", "")),
        _name(guild, entry.get("moderator")) if entry.get("moderator") else "—",
        human(timedelta(seconds=dur)) if dur else "—",
        (entry.get("detail") or "").replace("\n", " "),
    ]


def _build_txt(header: str, rows: list[list[str]]) -> bytes:
    lines = [header, "", " | ".join(_COLS), "-" * 88]
    lines += [" | ".join(r) for r in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_csv(rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_COLS)
    writer.writerows(rows)
    # BOM utf-8 pour un affichage correct des accents dans Excel.
    return buf.getvalue().encode("utf-8-sig")


def _build_pdf(header: str, rows: list[list[str]]) -> bytes:
    """Rend le journal en PDF paginé (bloquant : à lancer dans un thread)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    per_page = 34
    total_pages = max(1, math.ceil(len(rows) / per_page))
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        for page in range(total_pages):
            chunk = rows[page * per_page:(page + 1) * per_page]
            fig = plt.figure(figsize=(11.69, 8.27))  # A4 paysage
            fig.text(0.04, 0.96, header, fontsize=9, weight="bold", va="top")
            y = 0.90
            fig.text(0.04, y, " | ".join(_COLS), fontsize=6.5,
                     family="monospace", weight="bold")
            y -= 0.024
            for r in chunk:
                fig.text(0.04, y, " | ".join(r)[:150], fontsize=6,
                         family="monospace")
                y -= 0.024
            fig.text(0.96, 0.02, f"{page + 1}/{total_pages}", fontsize=7,
                     ha="right")
            pdf.savefig(fig)
            plt.close(fig)
    return buf.getvalue()


class Export(commands.Cog):
    """Export du journal de modération (owners du bot / propriétaire serveur)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="export",
        description="Exporte le journal de modération (txt/csv/pdf) sur une période.",
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="Texte (.txt)", value="txt"),
        app_commands.Choice(name="CSV (.csv)", value="csv"),
        app_commands.Choice(name="PDF (.pdf)", value="pdf"),
    ])
    @commands.guild_only()
    async def export(
        self, ctx: commands.Context, format: str, periode: str | None = None,
    ) -> None:
        # Réservé aux owners du bot et au propriétaire du serveur.
        if not checks.is_owner_or_server_owner(ctx):
            await ctx.send(t(ctx, "export.forbidden"))
            return

        fmt = format.lower().lstrip(".")
        if fmt not in _FORMATS:
            await ctx.send(t(ctx, "export.bad_format"))
            return

        # Période : « all » = tout l'historique, sinon une durée (défaut 30j).
        if periode and periode.lower() in _ALL:
            delta, since_ts = None, 0.0
            period_label = t(ctx, "export.all")
        else:
            delta = parse_duration(periode) if periode else timedelta(days=30)
            if delta is None:
                await ctx.send(t(ctx, "export.bad_period"))
                return
            since_ts = (datetime.now(timezone.utc) - delta).timestamp()
            period_label = human(delta)

        entries = [
            e for e in storage.get_guild_modlog(ctx.guild.id)
            if e.get("ts", 0) >= since_ts
        ]
        if not entries:
            await ctx.send(t(ctx, "export.no_data", period=period_label))
            return

        rows = [_row(ctx.guild, e) for e in entries]
        header = t(ctx, "export.header", guild=ctx.guild.name,
                   period=period_label, count=len(rows),
                   when=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

        async with ctx.typing():
            if fmt == "txt":
                data = _build_txt(header, rows)
            elif fmt == "csv":
                data = _build_csv(rows)
            else:  # pdf (génération bloquante déportée dans un thread)
                data = await asyncio.to_thread(_build_pdf, header, rows)

        filename = f"moderation-{ctx.guild.id}.{fmt}"
        log.info(
            "Export %s (%d entrées, %s) par %s (%s) sur %s (%s)",
            fmt, len(rows), period_label, ctx.author, ctx.author.id,
            ctx.guild.name, ctx.guild.id,
        )
        await ctx.send(
            t(ctx, "export.done", count=len(rows), period=period_label),
            file=discord.File(io.BytesIO(data), filename=filename),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Export(bot))
