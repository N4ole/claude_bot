"""Commande admin `ban` : bannit un utilisateur, avec raison et durée option.

    ban <utilisateur> [durée] [raison]

Si une durée est fournie (format court : 30s, 5m, 2h, 1d, 1h30m…), le
bannissement est temporaire : le membre est débanni automatiquement à
l'échéance. La temporisation est persistée sur disque et reprise au
redémarrage du bot. Sans durée, le bannissement est définitif.
"""
import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import storage
from utils.duration import parse_duration
from utils.i18n import t

log = logging.getLogger("action")


class Ban(commands.Cog):
    """Bannissement (permission « Bannir des membres »), permanent ou temporisé."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._resumed = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Reprend les bans temporaires persistés (une seule fois)."""
        if self._resumed:
            return
        self._resumed = True
        for guild_id, user_id, release_ts in storage.get_tempbans():
            self.bot.loop.create_task(
                self._schedule_unban(guild_id, user_id, release_ts)
            )

    async def _schedule_unban(
        self, guild_id: int, user_id: int, release_ts: float
    ) -> None:
        """Attend l'échéance puis débannit. Robuste au redémarrage."""
        delay = release_ts - datetime.now(timezone.utc).timestamp()
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            storage.clear_tempban(guild_id, user_id)
            return
        try:
            await guild.unban(
                discord.Object(id=user_id), reason="Fin du ban temporaire"
            )
            log.info(
                "Ban temporaire expiré — %s débanni de %s (%s)",
                user_id, guild.name, guild.id,
            )
        except discord.NotFound:
            pass  # déjà débanni manuellement.
        except discord.HTTPException:
            pass
        finally:
            storage.clear_tempban(guild_id, user_id)

    @commands.hybrid_command(
        name="ban",
        description="Bannit un utilisateur (raison et durée optionnelle).",
    )
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self, ctx: commands.Context, member: discord.Member,
        duree: str | None = None, *, raison: str | None = None,
    ) -> None:
        # La durée est optionnelle : si le 1er mot n'en est pas une, il fait
        # partie de la raison (ex: `ban @x spam` = ban définitif, raison spam).
        delta = None
        if duree is not None:
            delta = parse_duration(duree)
            if delta is None:
                raison = f"{duree} {raison}".strip() if raison else duree
                duree = None
        reason = raison or t(ctx, "mod.no_reason")

        # Garde-fous : soi-même et hiérarchie des rôles.
        if member.id == ctx.author.id:
            await ctx.send(t(ctx, "ban.self"))
            return
        if (
            ctx.author.id != ctx.guild.owner_id
            and member.top_role >= ctx.author.top_role
        ):
            await ctx.send(t(ctx, "ban.hierarchy"))
            return

        try:
            await ctx.guild.ban(
                member, reason=f"{ctx.author} : {reason}",
                delete_message_days=0,
            )
        except discord.Forbidden:
            await ctx.send(t(ctx, "ban.forbidden"))
            return
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "ban.failed", error=exc))
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "ban", ctx.author.id,
            duration=delta.total_seconds() if delta else None,
            detail=reason,
        )

        embed = discord.Embed(
            title=t(ctx, "ban.title"), color=discord.Color.red()
        )
        if delta is not None:
            until = discord.utils.utcnow() + delta
            release_ts = until.timestamp()
            storage.set_tempban(ctx.guild.id, member.id, release_ts)
            self.bot.loop.create_task(
                self._schedule_unban(ctx.guild.id, member.id, release_ts)
            )
            embed.description = t(ctx, "ban.temp_desc", user=str(member),
                                  reason=reason)
            embed.add_field(
                name=t(ctx, "ban.until"),
                value=discord.utils.format_dt(until, style="F"), inline=True,
            )
            embed.add_field(
                name=t(ctx, "ban.relative"),
                value=discord.utils.format_dt(until, style="R"), inline=True,
            )
            log.info(
                "Ban temporaire — %s (%s) banni par %s (%s) sur %s (%s) "
                "jusqu'au %s : %s",
                member, member.id, ctx.author, ctx.author.id,
                ctx.guild.name, ctx.guild.id, until.isoformat(), reason,
            )
        else:
            embed.description = t(ctx, "ban.perm_desc", user=str(member),
                                  reason=reason)
            log.info(
                "Ban définitif — %s (%s) banni par %s (%s) sur %s (%s) : %s",
                member, member.id, ctx.author, ctx.author.id,
                ctx.guild.name, ctx.guild.id, reason,
            )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
