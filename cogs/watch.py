"""Commande admin `watch` : surveille un utilisateur et journalise son activité.

Crée une catégorie « WATCHED USER » et un salon « {user} watched » (visible
uniquement par les administrateurs), puis y recopie :
  - les messages envoyés,
  - les messages modifiés (avant / après),
  - les messages supprimés,
  - les connexions / déconnexions vocales, avec l'heure et la durée de présence.
"""
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import storage
from utils.i18n import t

CATEGORY_NAME = "WATCHED USER"


def _fmt_duration(delta) -> str:
    """Formate une durée en 'Xh Ym Zs'."""
    total = int(delta.total_seconds())
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


class Watch(commands.Cog):
    """Surveillance d'utilisateurs (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # (guild_id, user_id) -> datetime d'entrée en vocal.
        self._voice_since: dict[tuple[int, int], datetime] = {}

    # ------------------------------------------------------------------ #
    # Utilitaires
    # ------------------------------------------------------------------ #
    def _log_channel(
        self, guild: discord.Guild, user_id: int
    ) -> discord.TextChannel | None:
        """Renvoie le salon de log d'un utilisateur surveillé, ou None."""
        channel_id = storage.get_channel_id(guild.id, user_id)
        if channel_id is None:
            return None
        return guild.get_channel(channel_id)

    # ------------------------------------------------------------------ #
    # Commandes
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="watch",
        description="Surveille un utilisateur et journalise son activité.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def watch(self, ctx: commands.Context, member: discord.Member) -> None:
        guild = ctx.guild

        if storage.get_channel_id(guild.id, member.id) is not None:
            await ctx.send(t(ctx, "watch.already", user=member.mention))
            return

        # Récupère (ou crée) la catégorie « WATCHED USER ».
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        # Salon visible uniquement par les administrateurs et le bot.
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        channel = await guild.create_text_channel(
            name=f"{member.name}-watched",
            category=category,
            overwrites=overwrites,
            topic=f"Surveillance de {member} (id: {member.id})",
        )

        storage.add_watch(guild.id, member.id, channel.id)
        await ctx.send(
            t(ctx, "watch.done", user=member.mention, channel=channel.mention)
        )

    @commands.hybrid_command(
        name="unwatch",
        description="Arrête la surveillance d'un utilisateur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unwatch(self, ctx: commands.Context, member: discord.Member) -> None:
        if storage.get_channel_id(ctx.guild.id, member.id) is None:
            await ctx.send(t(ctx, "unwatch.not", user=member.mention))
            return

        storage.remove_watch(ctx.guild.id, member.id)
        self._voice_since.pop((ctx.guild.id, member.id), None)
        await ctx.send(t(ctx, "unwatch.done", user=member.mention))

    @commands.hybrid_command(
        name="watchlist",
        description="Liste les utilisateurs actuellement surveillés.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def watchlist(self, ctx: commands.Context) -> None:
        watches = storage.get_guild_watches(ctx.guild.id)
        if not watches:
            await ctx.send(t(ctx, "watchlist.empty"))
            return

        lines = []
        for user_id, channel_id in watches.items():
            channel = ctx.guild.get_channel(channel_id)
            target = (
                channel.mention if channel
                else t(ctx, "watch.deleted", id=channel_id)
            )
            lines.append(f"• <@{user_id}> → {target}")

        embed = discord.Embed(
            title=t(ctx, "watchlist.title"),
            description="\n".join(lines),
            color=discord.Color.dark_red(),
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ #
    # Listeners
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        channel = self._log_channel(message.guild, message.author.id)
        if channel is None or channel.id == message.channel.id:
            return

        g = message.guild
        embed = discord.Embed(
            description=message.content or t(g, "watch.no_text"),
            color=discord.Color.blue(),
            timestamp=message.created_at,
        )
        embed.set_author(
            name=t(g, "watch.msg_sent", user=message.author),
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name=t(g, "watch.channel"),
                        value=message.channel.mention, inline=True)
        embed.add_field(
            name=t(g, "watch.link"),
            value=f"[{t(g, 'watch.goto')}]({message.jump_url})", inline=True,
        )
        if message.attachments:
            embed.add_field(
                name=t(g, "watch.attachments"),
                value="\n".join(a.url for a in message.attachments),
                inline=False,
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        if after.author.bot or after.guild is None:
            return
        if before.content == after.content:
            return
        channel = self._log_channel(after.guild, after.author.id)
        if channel is None or channel.id == after.channel.id:
            return

        g = after.guild
        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=t(g, "watch.msg_edit", user=after.author),
            icon_url=after.author.display_avatar.url,
        )
        embed.add_field(name=t(g, "watch.before"),
                        value=before.content or t(g, "watch.no_text"),
                        inline=False)
        embed.add_field(name=t(g, "watch.after"),
                        value=after.content or t(g, "watch.no_text"),
                        inline=False)
        embed.add_field(name=t(g, "watch.channel"),
                        value=after.channel.mention, inline=True)
        embed.add_field(
            name=t(g, "watch.link"),
            value=f"[{t(g, 'watch.goto')}]({after.jump_url})", inline=True,
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        channel = self._log_channel(message.guild, message.author.id)
        if channel is None or channel.id == message.channel.id:
            return

        g = message.guild
        embed = discord.Embed(
            description=message.content or t(g, "watch.no_text"),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=t(g, "watch.msg_del", user=message.author),
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name=t(g, "watch.channel"),
                        value=message.channel.mention, inline=True)
        if message.attachments:
            embed.add_field(
                name=t(g, "watch.attachments"),
                value="\n".join(a.url for a in message.attachments),
                inline=False,
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return
        channel = self._log_channel(member.guild, member.id)
        if channel is None:
            return

        key = (member.guild.id, member.id)
        now = datetime.now(timezone.utc)

        g = member.guild
        # Connexion à un salon vocal.
        if before.channel is None and after.channel is not None:
            self._voice_since[key] = now
            embed = discord.Embed(
                description=t(g, "watch.voice_join", channel=after.channel.name),
                color=discord.Color.green(),
                timestamp=now,
            )
            embed.set_author(name=t(g, "watch.voice", user=member),
                             icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

        # Déconnexion d'un salon vocal.
        elif before.channel is not None and after.channel is None:
            since = self._voice_since.pop(key, None)
            embed = discord.Embed(
                description=t(g, "watch.voice_leave",
                              channel=before.channel.name),
                color=discord.Color.dark_grey(),
                timestamp=now,
            )
            embed.set_author(name=t(g, "watch.voice", user=member),
                             icon_url=member.display_avatar.url)
            embed.add_field(
                name=t(g, "watch.leave_time"),
                value=discord.utils.format_dt(now, style="T"),
                inline=True,
            )
            if since is not None:
                embed.add_field(
                    name=t(g, "watch.duration"),
                    value=_fmt_duration(now - since),
                    inline=True,
                )
            await channel.send(embed=embed)

        # Changement de salon vocal.
        elif (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            embed = discord.Embed(
                description=t(g, "watch.voice_move",
                              before=before.channel.name,
                              after=after.channel.name),
                color=discord.Color.blurple(),
                timestamp=now,
            )
            embed.set_author(name=t(g, "watch.voice", user=member),
                             icon_url=member.display_avatar.url)
            await channel.send(embed=embed)

    # --- Réactions ------------------------------------------------------- #
    async def _log_reaction(
        self, payload: discord.RawReactionActionEvent, added: bool
    ) -> None:
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        channel = self._log_channel(guild, payload.user_id)
        if channel is None:
            return

        member = guild.get_member(payload.user_id)
        name = str(member) if member else f"ID {payload.user_id}"
        icon = member.display_avatar.url if member else None
        jump = (
            f"https://discord.com/channels/{payload.guild_id}"
            f"/{payload.channel_id}/{payload.message_id}"
        )

        desc_key = "watch.reaction_added" if added else "watch.reaction_removed"
        auth_key = "watch.reaction_add" if added else "watch.reaction_del"
        embed = discord.Embed(
            description=t(guild, desc_key, emoji=payload.emoji),
            color=discord.Color.teal() if added else discord.Color.dark_teal(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=t(guild, auth_key, user=name), icon_url=icon)
        embed.add_field(
            name=t(guild, "watch.message"),
            value=f"[{t(guild, 'watch.goto')}]({jump})", inline=True,
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        await self._log_reaction(payload, added=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        await self._log_reaction(payload, added=False)

    # --- Pseudo (nickname) ---------------------------------------------- #
    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if before.nick == after.nick:
            return
        channel = self._log_channel(after.guild, after.id)
        if channel is None:
            return

        g = after.guild
        embed = discord.Embed(
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=t(g, "watch.nick", user=after),
                         icon_url=after.display_avatar.url)
        embed.add_field(name=t(g, "watch.before"),
                        value=before.nick or t(g, "watch.none"), inline=True)
        embed.add_field(name=t(g, "watch.after"),
                        value=after.nick or t(g, "watch.none"), inline=True)
        await channel.send(embed=embed)

    # --- Statut ---------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_presence_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if before.status == after.status:
            return
        channel = self._log_channel(after.guild, after.id)
        if channel is None:
            return

        g = after.guild
        embed = discord.Embed(
            description=t(g, "watch.status_desc",
                          before=before.status, after=after.status),
            color=discord.Color.greyple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=t(g, "watch.status", user=after),
                         icon_url=after.display_avatar.url)
        await channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Watch(bot))
