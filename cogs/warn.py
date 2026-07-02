"""Commandes admin `warn` / `unwarn` / `warns` : système d'avertissements.

Barème des sanctions (un rôle « Warn N » reflète le niveau courant) :
  1 → simple avertissement
  2 → mute (timeout) 5 minutes
  3 → mute (timeout) 1 heure
  4 → confinement pendant une semaine
  5 → bannissement permanent
"""
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from utils import storage
from utils.i18n import t

log = logging.getLogger(__name__)

MAX_WARN = 5
CONFINE_DURATION = timedelta(weeks=1)


def _warn_role_name(level: int) -> str:
    return f"Warn {level}"


class Warn(commands.Cog):
    """Système d'avertissements progressifs (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Gestion des rôles de warn
    # ------------------------------------------------------------------ #
    async def _ensure_warn_role(
        self, guild: discord.Guild, level: int
    ) -> discord.Role | None:
        name = _warn_role_name(level)
        role = discord.utils.get(guild.roles, name=name)
        if role is not None:
            return role
        try:
            return await guild.create_role(
                name=name,
                permissions=discord.Permissions.none(),
                reason="Rôle d'avertissement",
            )
        except discord.HTTPException:
            log.warning("Impossible de créer le rôle %s", name)
            return None

    async def _sync_warn_role(
        self, member: discord.Member, level: int
    ) -> None:
        """Ne garde que le rôle « Warn <level> » (retire les autres)."""
        # Retire tous les rôles de warn existants.
        to_remove = [
            r for r in member.roles
            if r.name.startswith("Warn ") and r.name != _warn_role_name(level)
        ]
        if to_remove:
            try:
                await member.remove_roles(*to_remove, reason="Mise à jour warn")
            except discord.HTTPException:
                pass

        # Ajoute le rôle correspondant au niveau courant (si 1..MAX-1 ; au
        # niveau MAX l'utilisateur est banni, pas besoin de rôle).
        if 1 <= level < MAX_WARN:
            role = await self._ensure_warn_role(member.guild, level)
            if role is not None and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Avertissement")
                except discord.HTTPException:
                    pass

    # ------------------------------------------------------------------ #
    # Application des sanctions
    # ------------------------------------------------------------------ #
    async def _apply_sanction(
        self, ctx: commands.Context, member: discord.Member, level: int
    ) -> str:
        """Applique la sanction du niveau et renvoie sa description."""
        if level == 1:
            return t(ctx, "warn.s1")

        if level == 2:
            try:
                await member.timeout(
                    timedelta(minutes=5), reason="Warn 2"
                )
            except discord.HTTPException:
                pass
            return t(ctx, "warn.s2")

        if level == 3:
            try:
                await member.timeout(timedelta(hours=1), reason="Warn 3")
            except discord.HTTPException:
                pass
            return t(ctx, "warn.s3")

        if level == 4:
            confine_cog = self.bot.get_cog("Confine")
            if confine_cog is not None:
                # Confinement jusqu'à une date précise, persistée sur disque
                # et reprise automatiquement après un redémarrage du bot.
                until = datetime.now(timezone.utc) + CONFINE_DURATION
                await confine_cog.apply_temp_confinement(ctx.guild, member, until)
            return t(ctx, "warn.s4")

        # Niveau >= MAX_WARN : bannissement.
        try:
            await member.ban(reason="Warn 5 — bannissement permanent")
        except discord.HTTPException:
            return t(ctx, "warn.s5_fail")
        return t(ctx, "warn.s5")

    # ------------------------------------------------------------------ #
    # Commandes
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="warn",
        description="Avertit un utilisateur (sanction progressive).",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx: commands.Context, member: discord.Member) -> None:
        level = storage.add_warn(ctx.guild.id, member.id)
        await self._sync_warn_role(member, level)
        sanction = await self._apply_sanction(ctx, member, level)
        storage.add_modlog(
            ctx.guild.id, member.id, "warn", ctx.author.id,
            detail=f"warn {level}/{MAX_WARN} — {sanction}",
        )

        embed = discord.Embed(
            title=t(ctx, "warn.title"),
            description=t(ctx, "warn.desc", user=member.mention,
                          level=level, max=MAX_WARN),
            color=discord.Color.red(),
        )
        embed.add_field(name=t(ctx, "warn.field"), value=sanction, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="unwarn",
        description="Retire un avertissement à un utilisateur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unwarn(self, ctx: commands.Context, member: discord.Member) -> None:
        current = storage.get_warns(ctx.guild.id, member.id)
        if current <= 0:
            await ctx.send(t(ctx, "unwarn.none", user=member.mention))
            return

        new_level = current - 1
        storage.set_warns(ctx.guild.id, member.id, new_level)
        await self._sync_warn_role(member, new_level)

        # Lève les sanctions temporaires si on redescend en dessous du seuil.
        try:
            await member.timeout(None, reason="Retrait d'un avertissement")
        except discord.HTTPException:
            pass
        confine_cog = self.bot.get_cog("Confine")
        if confine_cog is not None:
            await confine_cog.remove_confinement(ctx.guild, member)

        await ctx.send(
            t(ctx, "unwarn.done", user=member.mention,
              level=new_level, max=MAX_WARN)
        )

    @commands.hybrid_command(
        name="warns",
        description="Affiche le nombre d'avertissements d'un utilisateur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def warns(self, ctx: commands.Context, member: discord.Member) -> None:
        count = storage.get_warns(ctx.guild.id, member.id)
        await ctx.send(
            t(ctx, "warns.count", user=member.mention, count=count, max=MAX_WARN)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warn(bot))
