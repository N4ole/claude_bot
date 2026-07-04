"""Commandes admin `confine` / `unconfine` : isole un utilisateur.

`confine` crée une catégorie « confinement » et un salon « confin-<user> »
où seul l'utilisateur ciblé (et les administrateurs) peut accéder, et retire
à l'utilisateur l'accès au reste du serveur.
`unconfine` restaure l'accès et supprime le salon de confinement.
"""
import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks, storage
from utils.i18n import t

log = logging.getLogger(__name__)

CATEGORY_NAME = "confinement"


class Confine(commands.Cog):
    """Confinement d'utilisateurs (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._resumed = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Reprend les confinements temporisés persistés (une seule fois)."""
        if self._resumed:
            return
        self._resumed = True
        for guild_id, user_id, release_ts in storage.get_confinements():
            self.bot.loop.create_task(
                self._schedule_release(guild_id, user_id, release_ts)
            )

    async def _schedule_release(
        self, guild_id: int, user_id: int, release_ts: float
    ) -> None:
        """Attend l'échéance puis libère le membre. Robuste au redémarrage."""
        delay = release_ts - datetime.now(timezone.utc).timestamp()
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            # Serveur inaccessible : on nettoie l'entrée pour éviter une
            # reprise infinie.
            storage.clear_confinement(guild_id, user_id)
            return
        member = guild.get_member(user_id)
        if member is not None:
            await self.remove_confinement(guild, member)
        else:
            storage.clear_confinement(guild_id, user_id)

    async def apply_temp_confinement(
        self, guild: discord.Guild, member: discord.Member, until: datetime
    ) -> None:
        """Confine un membre jusqu'à une date précise (persistée sur disque)."""
        await self.apply_confinement(guild, member)
        release_ts = until.timestamp()
        storage.set_confinement(guild.id, member.id, release_ts)
        self.bot.loop.create_task(
            self._schedule_release(guild.id, member.id, release_ts)
        )

    def _find_confine_channel(
        self, guild: discord.Guild, member_id: int
    ) -> discord.TextChannel | None:
        """Retrouve le salon de confinement d'un membre via son topic."""
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            return None
        marker = f"id: {member_id}"
        for channel in category.text_channels:
            if channel.topic and marker in channel.topic:
                return channel
        return None

    async def apply_confinement(
        self, guild: discord.Guild, member: discord.Member
    ) -> discord.TextChannel | None:
        """Confine un membre. Renvoie le salon créé, ou None si déjà confiné."""
        if self._find_confine_channel(guild, member.id) is not None:
            return None

        # Retire l'accès au reste du serveur : deny view_channel sur chaque
        # catégorie et sur les salons hors catégorie. Les salons synchronisés
        # avec leur catégorie héritent automatiquement de ce refus.
        deny = discord.PermissionOverwrite(view_channel=False)
        for category in guild.categories:
            try:
                await category.set_permissions(
                    member, overwrite=deny, reason="Confinement"
                )
            except discord.HTTPException:
                pass
        for channel in guild.channels:
            if channel.category is None:
                try:
                    await channel.set_permissions(
                        member, overwrite=deny, reason="Confinement"
                    )
                except discord.HTTPException:
                    pass

        # Crée (ou récupère) la catégorie de confinement, masquée à tous.
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(
                CATEGORY_NAME,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(
                        view_channel=False
                    )
                },
            )

        # Salon visible uniquement par l'utilisateur confiné et le bot
        # (les administrateurs y accèdent via leur permission).
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }
        channel = await guild.create_text_channel(
            name=f"confin-{member.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Confinement de {member} (id: {member.id})",
        )
        await channel.send(t(guild, "confine.notice", user=member.mention))
        return channel

    async def remove_confinement(
        self, guild: discord.Guild, member: discord.Member
    ) -> bool:
        """Libère un membre. Renvoie True si un confinement a été retiré."""
        channel = self._find_confine_channel(guild, member.id)

        # Retire une éventuelle temporisation persistée.
        storage.clear_confinement(guild.id, member.id)

        # Restaure l'accès : retire les overwrites de refus posés sur le membre.
        for category in guild.categories:
            if not category.overwrites_for(member).is_empty():
                try:
                    await category.set_permissions(
                        member, overwrite=None, reason="Fin du confinement"
                    )
                except discord.HTTPException:
                    pass
        for chan in guild.channels:
            if chan.category is None and not chan.overwrites_for(member).is_empty():
                try:
                    await chan.set_permissions(
                        member, overwrite=None, reason="Fin du confinement"
                    )
                except discord.HTTPException:
                    pass

        if channel is not None:
            category = channel.category
            await channel.delete(reason="Fin du confinement")
            if category is not None and not category.channels:
                await category.delete(reason="Confinement vide")
            return True
        return False

    @commands.hybrid_command(
        name="confine",
        description="Isole un utilisateur dans un salon de confinement.",
    )
    @checks.admin()
    async def confine(self, ctx: commands.Context, member: discord.Member) -> None:
        channel = await self.apply_confinement(ctx.guild, member)
        if channel is None:
            await ctx.send(t(ctx, "confine.already", user=member.mention))
            return
        storage.add_modlog(ctx.guild.id, member.id, "confine", ctx.author.id)
        await ctx.send(
            t(ctx, "confine.done", user=member.mention, channel=channel.mention)
        )

    @commands.hybrid_command(
        name="unconfine",
        description="Libère un utilisateur du confinement.",
    )
    @checks.admin()
    async def unconfine(self, ctx: commands.Context, member: discord.Member) -> None:
        await self.remove_confinement(ctx.guild, member)
        await ctx.send(t(ctx, "unconfine.done", user=member.mention))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Confine(bot))
