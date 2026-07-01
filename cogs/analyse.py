"""Commande admin `analyse` : graphique d'activité du serveur sur 7 jours.

Collecte en continu (messages, arrivées/départs, nombre de membres) et génère
un graphique en barres : membres, messages par membre et par jour, join/leave.
"""
import io
import logging
from collections import defaultdict

import discord
from discord.ext import commands, tasks

from utils import analytics

log = logging.getLogger(__name__)

PERIOD_DAYS = 7


class Analyse(commands.Cog):
    """Analytics du serveur (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Tampon en mémoire pour éviter d'écrire à chaque message.
        self._buffer: dict[int, dict[str, int]] = defaultdict(
            lambda: {"messages": 0, "joins": 0, "leaves": 0}
        )

    async def cog_load(self) -> None:
        self._flush.start()

    async def cog_unload(self) -> None:
        self._flush.cancel()

    # ------------------------------------------------------------------ #
    # Collecte
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        self._buffer[message.guild.id]["messages"] += 1

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        self._buffer[member.guild.id]["joins"] += 1

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        self._buffer[member.guild.id]["leaves"] += 1

    @tasks.loop(minutes=1)
    async def _flush(self) -> None:
        self._do_flush()

    @_flush.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()

    def _do_flush(self) -> None:
        """Écrit le tampon sur disque et met à jour le nombre de membres."""
        buffer, self._buffer = self._buffer, defaultdict(
            lambda: {"messages": 0, "joins": 0, "leaves": 0}
        )
        for guild_id, counts in buffer.items():
            analytics.add_counts(
                guild_id,
                messages=counts["messages"],
                joins=counts["joins"],
                leaves=counts["leaves"],
            )
        for guild in self.bot.guilds:
            analytics.set_members(guild.id, guild.member_count or 0)

    # ------------------------------------------------------------------ #
    # Rendu du graphique
    # ------------------------------------------------------------------ #
    @staticmethod
    def _render(data: list[dict], guild_name: str) -> bytes:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [d["date"][5:] for d in data]  # MM-DD
        members = [d["members"] for d in data]
        msg_per_member = [
            round(d["messages"] / d["members"], 2) if d["members"] else 0
            for d in data
        ]
        joins = [d["joins"] for d in data]
        leaves = [d["leaves"] for d in data]

        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1, figsize=(9, 10), constrained_layout=True
        )
        fig.suptitle(f"Analyse de {guild_name} — 7 jours", fontsize=15)

        ax1.bar(labels, members, color="#5865F2")
        ax1.set_title("Nombre de membres")

        ax2.bar(labels, msg_per_member, color="#57F287")
        ax2.set_title("Messages par membre et par jour")

        x = range(len(labels))
        ax3.bar([i - 0.2 for i in x], joins, width=0.4, label="Arrivées",
                color="#3BA55D")
        ax3.bar([i + 0.2 for i in x], leaves, width=0.4, label="Départs",
                color="#ED4245")
        ax3.set_xticks(list(x))
        ax3.set_xticklabels(labels)
        ax3.set_title("Arrivées / Départs")
        ax3.legend()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # ------------------------------------------------------------------ #
    # Commande
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="analyse",
        description="Graphique d'activité du serveur sur 7 jours.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def analyse(self, ctx: commands.Context) -> None:
        await ctx.defer()
        # On vide le tampon pour inclure les données les plus récentes.
        self._do_flush()
        data = analytics.get_range(ctx.guild.id, PERIOD_DAYS)

        image = await self.bot.loop.run_in_executor(
            None, self._render, data, ctx.guild.name
        )
        file = discord.File(io.BytesIO(image), filename="analyse.png")
        embed = discord.Embed(
            title="📈 Analyse du serveur (7 jours)",
            color=discord.Color.blurple(),
        )
        embed.set_image(url="attachment://analyse.png")
        await ctx.send(embed=embed, file=file)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Analyse(bot))
