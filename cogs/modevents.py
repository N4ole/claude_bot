"""Journalise la modération faite HORS commande du bot (via l'app Discord).

Complète le cog `logs` (qui ne consigne que les commandes du bot) : quand un
modérateur agit directement dans Discord (clic droit « Supprimer le message »,
bannir/expulser depuis le menu, débannir…), l'action est consignée dans le
salon de logs « mod » du serveur, s'il est activé.

Déduplication : les actions déclenchées par le bot lui-même (commandes,
automod) sont ignorées ici — elles sont déjà journalisées par leur cog. On
identifie l'auteur réel via les logs d'audit Discord ; si c'est le bot, on
n'écrit rien.
"""
import discord
from discord.ext import commands

from utils import logchannels, storage
from utils.i18n import t

# Fenêtre (secondes) pendant laquelle une entrée d'audit est jugée liée à
# l'événement gateway qu'on vient de recevoir.
_AUDIT_MAX_AGE = 15


class ModEvents(commands.Cog):
    """Logs des actions de modération faites hors commande du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        return logchannels.log_channel(guild, "mod")

    async def _recent_executor(
        self, guild: discord.Guild, action: discord.AuditLogAction,
        target_id: int | None,
    ) -> tuple[discord.abc.User | None, str | None]:
        """Auteur (et raison) d'une action récente via les logs d'audit.

        Best-effort : renvoie (None, None) si l'audit est inaccessible ou si
        aucune entrée récente ne correspond à la cible.
        """
        me = guild.me
        if me is None or not me.guild_permissions.view_audit_log:
            return None, None
        try:
            async for entry in guild.audit_logs(limit=8, action=action):
                if target_id is not None and (
                    entry.target is None or entry.target.id != target_id
                ):
                    continue
                age = (
                    discord.utils.utcnow() - entry.created_at
                ).total_seconds()
                if age <= _AUDIT_MAX_AGE:
                    return entry.user, entry.reason
                return None, None
        except (discord.Forbidden, discord.HTTPException):
            return None, None
        return None, None

    def _is_self(self, user: discord.abc.User | None) -> bool:
        """True si l'auteur est le bot (action déjà journalisée ailleurs)."""
        return user is not None and self.bot.user is not None \
            and user.id == self.bot.user.id

    async def _send(self, guild: discord.Guild, embed: discord.Embed) -> None:
        channel = self._channel(guild)
        if channel is None:
            return
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @staticmethod
    def _actor(user: discord.abc.User | None, guild: discord.Guild) -> str:
        if user is None:
            return t(guild, "modev.unknown")
        return f"{user.mention} (`{user.id}`)"

    # --------------------------------------------------------------------- #
    # Suppression de message (ex. clic droit « Supprimer le message »)
    # --------------------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        # N'écrit pas dans la catégorie de logs elle-même (évite la récursion).
        category = getattr(message.channel, "category", None)
        if category is not None and category.name == logchannels.CATEGORY_NAME:
            return
        if self._channel(message.guild) is None:
            return
        # On ne consigne que les suppressions faites PAR un modérateur (l'audit
        # ne trace pas les auto-suppressions) : sinon trop de bruit.
        executor, _ = await self._recent_executor(
            message.guild, discord.AuditLogAction.message_delete,
            message.author.id,
        )
        if executor is None or self._is_self(executor):
            return

        embed = discord.Embed(
            title=t(message.guild, "modev.msg_del_title"),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(message.guild, "modev.f_author"),
                        value=f"{message.author.mention} "
                              f"(`{message.author.id}`)", inline=True)
        embed.add_field(name=t(message.guild, "modev.f_by"),
                        value=self._actor(executor, message.guild), inline=True)
        embed.add_field(name=t(message.guild, "modev.f_channel"),
                        value=getattr(message.channel, "mention", "?"),
                        inline=True)
        content = message.content or t(message.guild, "modev.no_content")
        embed.add_field(name=t(message.guild, "modev.f_content"),
                        value=content[:1024], inline=False)
        if message.attachments:
            embed.add_field(
                name=t(message.guild, "modev.f_attachments"),
                value=str(len(message.attachments)), inline=True,
            )
        await self._send(message.guild, embed)

    # --------------------------------------------------------------------- #
    # Bannissement / débannissement manuels
    # --------------------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_member_ban(
        self, guild: discord.Guild, user: discord.abc.User
    ) -> None:
        if self._channel(guild) is None:
            return
        executor, reason = await self._recent_executor(
            guild, discord.AuditLogAction.ban, user.id
        )
        # Auteur inconnu (audit illisible) ou bot : on n'écrit rien, pour ne
        # jamais dupliquer un ban déclenché par une commande du bot.
        if executor is None or self._is_self(executor):
            return
        storage.add_modlog(
            guild.id, user.id, "ban",
            executor.id if executor else None, detail=reason,
        )
        embed = discord.Embed(
            title=t(guild, "modev.ban_title"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(guild, "modev.f_member"),
                        value=f"{user} (`{user.id}`)", inline=True)
        embed.add_field(name=t(guild, "modev.f_by"),
                        value=self._actor(executor, guild), inline=True)
        if reason:
            embed.add_field(name=t(guild, "modev.f_reason"), value=reason,
                            inline=False)
        await self._send(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(
        self, guild: discord.Guild, user: discord.abc.User
    ) -> None:
        if self._channel(guild) is None:
            return
        executor, reason = await self._recent_executor(
            guild, discord.AuditLogAction.unban, user.id
        )
        if executor is None or self._is_self(executor):
            return
        storage.add_modlog(
            guild.id, user.id, "unban",
            executor.id if executor else None, detail=reason,
        )
        embed = discord.Embed(
            title=t(guild, "modev.unban_title"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(guild, "modev.f_member"),
                        value=f"{user} (`{user.id}`)", inline=True)
        embed.add_field(name=t(guild, "modev.f_by"),
                        value=self._actor(executor, guild), inline=True)
        await self._send(guild, embed)

    # --------------------------------------------------------------------- #
    # Expulsion manuelle (distinguée d'un simple départ via l'audit)
    # --------------------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if self._channel(member.guild) is None:
            return
        executor, reason = await self._recent_executor(
            member.guild, discord.AuditLogAction.kick, member.id
        )
        # Pas d'entrée d'audit récente = départ volontaire, pas une expulsion.
        if executor is None or self._is_self(executor):
            return
        storage.add_modlog(
            member.guild.id, member.id, "kick", executor.id, detail=reason
        )
        embed = discord.Embed(
            title=t(member.guild, "modev.kick_title"),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(member.guild, "modev.f_member"),
                        value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name=t(member.guild, "modev.f_by"),
                        value=self._actor(executor, member.guild), inline=True)
        if reason:
            embed.add_field(name=t(member.guild, "modev.f_reason"),
                            value=reason, inline=False)
        await self._send(member.guild, embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModEvents(bot))
