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
            await ctx.send(f"⚠️ {member.mention} est déjà surveillé.")
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
            f"👁️ Surveillance de {member.mention} activée dans {channel.mention}."
        )

    @commands.hybrid_command(
        name="unwatch",
        description="Arrête la surveillance d'un utilisateur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def unwatch(self, ctx: commands.Context, member: discord.Member) -> None:
        if storage.get_channel_id(ctx.guild.id, member.id) is None:
            await ctx.send(f"⚠️ {member.mention} n'est pas surveillé.")
            return

        storage.remove_watch(ctx.guild.id, member.id)
        self._voice_since.pop((ctx.guild.id, member.id), None)
        await ctx.send(
            f"✅ Surveillance de {member.mention} arrêtée. "
            "(Le salon de log n'est pas supprimé.)"
        )

    @commands.hybrid_command(
        name="watchlist",
        description="Liste les utilisateurs actuellement surveillés.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def watchlist(self, ctx: commands.Context) -> None:
        watches = storage.get_guild_watches(ctx.guild.id)
        if not watches:
            await ctx.send("Aucun utilisateur n'est surveillé sur ce serveur.")
            return

        lines = []
        for user_id, channel_id in watches.items():
            channel = ctx.guild.get_channel(channel_id)
            target = channel.mention if channel else f"#{channel_id} (supprimé)"
            lines.append(f"• <@{user_id}> → {target}")

        embed = discord.Embed(
            title="👁️ Utilisateurs surveillés",
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

        embed = discord.Embed(
            description=message.content or "*(aucun texte)*",
            color=discord.Color.blue(),
            timestamp=message.created_at,
        )
        embed.set_author(
            name=f"{message.author} — message envoyé",
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        embed.add_field(
            name="Lien", value=f"[aller au message]({message.jump_url})", inline=True
        )
        if message.attachments:
            embed.add_field(
                name="Pièces jointes",
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

        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{after.author} — message modifié",
            icon_url=after.author.display_avatar.url,
        )
        embed.add_field(
            name="Avant", value=before.content or "*(aucun texte)*", inline=False
        )
        embed.add_field(
            name="Après", value=after.content or "*(aucun texte)*", inline=False
        )
        embed.add_field(name="Salon", value=after.channel.mention, inline=True)
        embed.add_field(
            name="Lien", value=f"[aller au message]({after.jump_url})", inline=True
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        channel = self._log_channel(message.guild, message.author.id)
        if channel is None or channel.id == message.channel.id:
            return

        embed = discord.Embed(
            description=message.content or "*(aucun texte)*",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{message.author} — message supprimé",
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        if message.attachments:
            embed.add_field(
                name="Pièces jointes",
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

        # Connexion à un salon vocal.
        if before.channel is None and after.channel is not None:
            self._voice_since[key] = now
            embed = discord.Embed(
                description=f"🔊 A rejoint **{after.channel.name}**",
                color=discord.Color.green(),
                timestamp=now,
            )
            embed.set_author(
                name=f"{member} — vocal",
                icon_url=member.display_avatar.url,
            )
            await channel.send(embed=embed)

        # Déconnexion d'un salon vocal.
        elif before.channel is not None and after.channel is None:
            since = self._voice_since.pop(key, None)
            embed = discord.Embed(
                description=f"🔇 A quitté **{before.channel.name}**",
                color=discord.Color.dark_grey(),
                timestamp=now,
            )
            embed.set_author(
                name=f"{member} — vocal",
                icon_url=member.display_avatar.url,
            )
            embed.add_field(
                name="Heure de sortie",
                value=discord.utils.format_dt(now, style="T"),
                inline=True,
            )
            if since is not None:
                embed.add_field(
                    name="Durée de présence",
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
                description=(
                    f"↔️ Est passé de **{before.channel.name}** "
                    f"à **{after.channel.name}**"
                ),
                color=discord.Color.blurple(),
                timestamp=now,
            )
            embed.set_author(
                name=f"{member} — vocal",
                icon_url=member.display_avatar.url,
            )
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

        verb = "ajoutée" if added else "retirée"
        embed = discord.Embed(
            description=f"Réaction {verb} : {payload.emoji}",
            color=discord.Color.teal() if added else discord.Color.dark_teal(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=f"{name} — réaction {verb}", icon_url=icon)
        embed.add_field(
            name="Message", value=f"[aller au message]({jump})", inline=True
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

        embed = discord.Embed(
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{after} — pseudo modifié",
            icon_url=after.display_avatar.url,
        )
        embed.add_field(
            name="Avant", value=before.nick or "*(aucun)*", inline=True
        )
        embed.add_field(
            name="Après", value=after.nick or "*(aucun)*", inline=True
        )
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

        embed = discord.Embed(
            description=f"Statut : **{before.status}** → **{after.status}**",
            color=discord.Color.greyple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{after} — statut modifié",
            icon_url=after.display_avatar.url,
        )
        await channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Watch(bot))
