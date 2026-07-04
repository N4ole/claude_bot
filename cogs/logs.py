"""Commande admin `logs <on|off> <type>` : journalisation Discord par type.

Les types correspondent aux catégories du help (général, info, util, mod,
owner). À l'activation d'un type, le bot crée (si besoin) une catégorie
« logs » puis un salon par type activé, où il consigne chaque commande de
cette catégorie (qui, quoi, où, comment). Chaque type s'active/désactive
indépendamment ; `all` agit sur tous les types.
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils import appchoices, categories, checks, storage
from utils.i18n import t

log = logging.getLogger("action")

CATEGORY_NAME = "logs"
SETTING = "logtypes"  # {token: channel_id}

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}
_STATUS = {"status", "statut", "état", "etat", "list", "liste", "info"}

# Choix slash pour le type de log : les catégories du help + « Tous ».
_CAT_CHOICES = [
    app_commands.Choice(name=t(None, cat_key), value=token)
    for token, cat_key in categories.TYPE_TO_CAT.items()
] + [app_commands.Choice(name="Tous / All", value="all")]


def _types_list() -> str:
    return ", ".join([f"`{token}`" for token in categories.TYPE_TO_CAT] + ["`all`"])


class Logs(commands.Cog):
    """Journalisation Discord des commandes, par catégorie (admins)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _enabled(self, guild_id: int) -> dict:
        return storage.get_setting(guild_id, SETTING, {}) or {}

    async def _send_status(self, ctx: commands.Context) -> None:
        """Affiche l'état (activé/désactivé) de chaque type de log."""
        enabled = self._enabled(ctx.guild.id)
        lines = []
        for token, cat_key in categories.TYPE_TO_CAT.items():
            channel_id = enabled.get(token)
            if channel_id:
                channel = ctx.guild.get_channel(channel_id)
                state = channel.mention if channel \
                    else t(ctx, "logs.st_on_nochan")
            else:
                state = t(ctx, "logs.st_off")
            lines.append(f"**{t(ctx, cat_key)}** — {state}")
        embed = discord.Embed(
            title=t(ctx, "logs.status_title"),
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        active = sum(1 for token in categories.TYPE_TO_CAT if enabled.get(token))
        embed.set_footer(text=t(ctx, "logs.status_footer", active=active,
                                total=len(categories.TYPE_TO_CAT)))
        await ctx.send(embed=embed)

    async def _ensure_category(
        self, guild: discord.Guild
    ) -> discord.CategoryChannel:
        """Crée/récupère la catégorie « logs », masquée à @everyone."""
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                ),
            }
            category = await guild.create_category(
                CATEGORY_NAME, overwrites=overwrites, reason="Logs"
            )
        return category

    async def _ensure_channel(
        self, guild: discord.Guild, token: str
    ) -> discord.TextChannel:
        category = await self._ensure_category(guild)
        name = f"logs-{token}"
        channel = discord.utils.get(category.text_channels, name=name)
        if channel is None:
            channel = await guild.create_text_channel(
                name, category=category, reason=f"Logs {token}"
            )
        return channel

    @commands.hybrid_command(
        name="logs",
        description="Active/désactive les logs Discord par type, ou `status`.",
    )
    @app_commands.choices(
        etat=appchoices.onoff() + [
            app_commands.Choice(name="Statut / Status", value="status"),
        ],
        categorie=_CAT_CHOICES,
    )
    @checks.admin()
    @commands.bot_has_permissions(manage_channels=True)
    async def logs(
        self, ctx: commands.Context, etat: str, categorie: str | None = None
    ) -> None:
        value = etat.lower()

        # `logs status` : état de chaque type de log.
        if value in _STATUS:
            await self._send_status(ctx)
            return

        if categorie is None:
            await ctx.send(t(ctx, "logs.usage",
                             prefix=ctx.prefix or config.PREFIX,
                             types=_types_list()))
            return
        raw = categorie.lower().strip()

        if raw == "all":
            tokens = list(categories.TYPE_TO_CAT)
        else:
            token = categories.resolve_type(raw)
            if token is None:
                await ctx.send(t(ctx, "logs.bad_type", types=_types_list()))
                return
            tokens = [token]

        if value in _ON:
            enabled = dict(self._enabled(ctx.guild.id))
            last = None
            for token in tokens:
                channel = await self._ensure_channel(ctx.guild, token)
                enabled[token] = channel.id
                last = channel
            storage.set_setting(ctx.guild.id, SETTING, enabled)
            log.info(
                "Logs %s activés sur %s (%s) par %s",
                ",".join(tokens), ctx.guild.name, ctx.guild.id, ctx.author,
            )
            if len(tokens) > 1:
                await ctx.send(t(ctx, "logs.on_all"))
            else:
                cat_key = categories.TYPE_TO_CAT[tokens[0]]
                await ctx.send(t(ctx, "logs.on", type=t(ctx, cat_key),
                                 channel=last.mention))

        elif value in _OFF:
            enabled = dict(self._enabled(ctx.guild.id))
            removed = False
            for token in tokens:
                if token in enabled:
                    channel = ctx.guild.get_channel(enabled.pop(token))
                    removed = True
                    if channel is not None:
                        try:
                            await channel.delete(reason="Logs désactivés")
                        except discord.HTTPException:
                            pass
            storage.set_setting(ctx.guild.id, SETTING, enabled)
            # Supprime la catégorie si plus aucun salon de log.
            category = discord.utils.get(ctx.guild.categories, name=CATEGORY_NAME)
            if category is not None and not category.channels:
                try:
                    await category.delete(reason="Logs vides")
                except discord.HTTPException:
                    pass
            if len(tokens) > 1:
                await ctx.send(t(ctx, "logs.off_all"))
            elif removed:
                await ctx.send(t(ctx, "logs.off",
                                 type=t(ctx, categories.TYPE_TO_CAT[tokens[0]])))
            else:
                await ctx.send(t(ctx, "logs.already_off",
                                 type=t(ctx, categories.TYPE_TO_CAT[tokens[0]])))
        else:
            await ctx.send(t(ctx, "logs.usage",
                             prefix=ctx.prefix or config.PREFIX,
                             types=_types_list()))

    @logs.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(t(ctx, "logs.usage",
                             prefix=ctx.prefix or config.PREFIX,
                             types=_types_list()))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))

    # ----------------------------------------------------------------- #
    # Routage des événements vers le salon de log de leur catégorie
    # ----------------------------------------------------------------- #
    def _log_channel(
        self, guild: discord.Guild, command: commands.Command
    ) -> discord.TextChannel | None:
        cat_key, _ = categories.category_of(command)
        token = categories.CAT_TO_TYPE.get(cat_key)
        if token is None:
            return None
        channel_id = self._enabled(guild.id).get(token)
        if not channel_id:
            return None
        # Salon éventuellement supprimé : get_channel renvoie alors None.
        channel = guild.get_channel(channel_id)
        return channel if hasattr(channel, "send") else None

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        if ctx.guild is None or ctx.command is None:
            return
        channel = self._log_channel(ctx.guild, ctx.command)
        if channel is None:
            return
        embed = discord.Embed(
            title=t(ctx.guild, "logs.entry_cmd", prefix=config.PREFIX,
                    cmd=ctx.command.qualified_name),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(ctx.guild, "logs.f_user"),
                        value=f"{ctx.author.mention} (`{ctx.author.id}`)",
                        inline=True)
        embed.add_field(name=t(ctx.guild, "logs.f_channel"),
                        value=getattr(ctx.channel, "mention", "?"), inline=True)
        via = "slash `/`" if ctx.interaction is not None else \
            f"préfixe `{ctx.prefix or config.PREFIX}`"
        embed.add_field(name=t(ctx.guild, "logs.f_via"), value=via, inline=True)
        params = " ".join(str(v) for v in ctx.kwargs.values()) if ctx.kwargs \
            else ""
        if params:
            embed.add_field(name=t(ctx.guild, "logs.f_args"),
                            value=params[:1024], inline=False)
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if ctx.guild is None or ctx.command is None:
            return
        if isinstance(error, commands.CommandNotFound):
            return
        channel = self._log_channel(ctx.guild, ctx.command)
        if channel is None:
            return
        embed = discord.Embed(
            title=t(ctx.guild, "logs.entry_error", prefix=config.PREFIX,
                    cmd=ctx.command.qualified_name),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=t(ctx.guild, "logs.f_user"),
                        value=f"{ctx.author.mention} (`{ctx.author.id}`)",
                        inline=True)
        embed.add_field(name=t(ctx.guild, "logs.f_channel"),
                        value=getattr(ctx.channel, "mention", "?"), inline=True)
        embed.add_field(name=t(ctx.guild, "logs.f_error"),
                        value=f"`{type(error).__name__}`", inline=False)
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logs(bot))
