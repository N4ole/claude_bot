"""Messages de bienvenue / d'au revoir + message de bienvenue en MP.

Configuration par serveur via le groupe de commandes `bienvenue` (admin) :
  - `bienvenue salon [#salon]`  salon des messages arrivée/départ (vide = off)
  - `bienvenue message [texte]` message d'arrivée (vide = message par défaut)
  - `bienvenue aurevoir [texte]` message de départ (vide = défaut)
  - `bienvenue mp <on|off>`     active/désactive le MP de bienvenue
  - `bienvenue mpmessage [texte]` message du MP (vide = défaut)
  - `bienvenue config`          affiche la configuration actuelle

Placeholders disponibles dans les messages : {user} (mention), {name} (pseudo),
{server} (nom du serveur), {count} (nombre de membres).
"""
import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, storage
from utils.i18n import t

# Clés de réglage (guild_settings).
K_CHANNEL = "welcome_channel"
K_JOIN = "welcome_msg"
K_LEAVE = "goodbye_msg"
K_DM = "welcome_dm"
K_DM_MSG = "welcome_dm_msg"

MAX_LEN = 1500

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}


def _render(template: str, member: discord.Member) -> str:
    """Remplace les placeholders du modèle (sans str.format, sûr aux accolades)."""
    return (
        template
        .replace("{user}", member.mention)
        .replace("{name}", member.display_name)
        .replace("{server}", member.guild.name)
        .replace("{count}", str(member.guild.member_count or 0))
    )


class Welcome(commands.Cog):
    """Messages d'arrivée/départ et MP de bienvenue (admins)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ #
    # Configuration
    # ------------------------------------------------------------------ #
    @commands.hybrid_group(
        name="bienvenue",
        description="Configure les messages de bienvenue/au revoir.",
    )
    @checks.admin()
    async def bienvenue(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await self._show_config(ctx)

    @bienvenue.command(name="salon",
                       description="Salon des messages arrivée/départ (vide = off).")
    @checks.admin()
    async def salon(
        self, ctx: commands.Context,
        salon: discord.TextChannel | None = None,
    ) -> None:
        if salon is None:
            storage.set_setting(ctx.guild.id, K_CHANNEL, None)
            await ctx.send(t(ctx, "welcome.channel_off"))
            return
        storage.set_setting(ctx.guild.id, K_CHANNEL, salon.id)
        await ctx.send(t(ctx, "welcome.channel_set", channel=salon.mention))

    @bienvenue.command(name="message",
                       description="Message d'arrivée (vide = message par défaut).")
    @checks.admin()
    async def message(
        self, ctx: commands.Context, *, texte: str | None = None
    ) -> None:
        await self._set_text(ctx, K_JOIN, texte, "welcome.join_set",
                             "welcome.join_reset")

    @bienvenue.command(name="aurevoir",
                       description="Message de départ (vide = message par défaut).")
    @checks.admin()
    async def aurevoir(
        self, ctx: commands.Context, *, texte: str | None = None
    ) -> None:
        await self._set_text(ctx, K_LEAVE, texte, "welcome.leave_set",
                             "welcome.leave_reset")

    @bienvenue.command(name="mp",
                       description="Active/désactive le MP de bienvenue (on/off).")
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def mp(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, K_DM, True)
            await ctx.send(t(ctx, "welcome.dm_on"))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, K_DM, False)
            await ctx.send(t(ctx, "welcome.dm_off"))
        else:
            await ctx.send(t(ctx, "toggle.usage", name="bienvenue mp"))

    @bienvenue.command(name="mpmessage",
                       description="Message du MP de bienvenue (vide = défaut).")
    @checks.admin()
    async def mpmessage(
        self, ctx: commands.Context, *, texte: str | None = None
    ) -> None:
        await self._set_text(ctx, K_DM_MSG, texte, "welcome.dm_set",
                             "welcome.dm_reset")

    @bienvenue.command(name="config",
                       description="Affiche la configuration de bienvenue.")
    @checks.admin()
    async def config_cmd(self, ctx: commands.Context) -> None:
        await self._show_config(ctx)

    async def _set_text(
        self, ctx: commands.Context, key: str, texte: str | None,
        set_key: str, reset_key: str,
    ) -> None:
        if texte is not None and len(texte) > MAX_LEN:
            await ctx.send(t(ctx, "welcome.too_long", max=MAX_LEN))
            return
        storage.set_setting(ctx.guild.id, key, texte.strip() if texte else None)
        await ctx.send(t(ctx, reset_key if not texte else set_key))

    async def _show_config(self, ctx: commands.Context) -> None:
        gid = ctx.guild.id
        channel_id = storage.get_setting(gid, K_CHANNEL)
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        dm_on = storage.get_setting(gid, K_DM, False)
        embed = discord.Embed(
            title=t(ctx, "welcome.cfg_title"),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name=t(ctx, "welcome.cfg_channel"),
            value=channel.mention if channel else t(ctx, "welcome.cfg_none"),
            inline=False,
        )
        embed.add_field(
            name=t(ctx, "welcome.cfg_join"),
            value=(storage.get_setting(gid, K_JOIN) or t(ctx, "welcome.default_join")),
            inline=False,
        )
        embed.add_field(
            name=t(ctx, "welcome.cfg_leave"),
            value=(storage.get_setting(gid, K_LEAVE) or t(ctx, "welcome.default_leave")),
            inline=False,
        )
        embed.add_field(
            name=t(ctx, "welcome.cfg_dm"),
            value=t(ctx, "welcome.cfg_on" if dm_on else "welcome.cfg_off"),
            inline=True,
        )
        embed.add_field(
            name=t(ctx, "welcome.cfg_dm_msg"),
            value=(storage.get_setting(gid, K_DM_MSG) or t(ctx, "welcome.default_dm")),
            inline=False,
        )
        embed.set_footer(text=t(ctx, "welcome.cfg_placeholders"))
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ #
    # Événements
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        gid = member.guild.id
        # Message dans le salon configuré.
        channel_id = storage.get_setting(gid, K_CHANNEL)
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel is not None and hasattr(channel, "send"):
                template = storage.get_setting(gid, K_JOIN) \
                    or t(member.guild, "welcome.default_join")
                try:
                    await channel.send(_render(template, member))
                except discord.HTTPException:
                    pass
        # MP de bienvenue.
        if storage.get_setting(gid, K_DM, False):
            template = storage.get_setting(gid, K_DM_MSG) \
                or t(member.guild, "welcome.default_dm")
            try:
                await member.send(_render(template, member))
            except (discord.HTTPException, discord.Forbidden):
                pass  # MP fermés : rien à faire.

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.bot:
            return
        channel_id = storage.get_setting(member.guild.id, K_CHANNEL)
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel is None or not hasattr(channel, "send"):
            return
        template = storage.get_setting(member.guild.id, K_LEAVE) \
            or t(member.guild, "welcome.default_leave")
        try:
            await channel.send(_render(template, member))
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
