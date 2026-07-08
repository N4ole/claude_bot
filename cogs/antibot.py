"""Commande admin `antibot on/off` : empêche les bots de rejoindre le serveur."""
import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils import appchoices, checks, embeds, logchannels, storage
from utils.i18n import t

log = logging.getLogger(__name__)

_ON = {"on", "activer", "enable", "true", "1"}
_OFF = {"off", "désactiver", "desactiver", "disable", "false", "0"}


class AntiBot(commands.Cog):
    """Expulse automatiquement les bots qui rejoignent (si activé)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="antibot",
        description="Active/désactive le blocage des bots (on/off).",
    )
    @app_commands.choices(etat=appchoices.onoff())
    @checks.admin()
    async def antibot(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, "antibot", True)
            await ctx.send(embed=embeds.success(t(ctx, "antibot.on")))
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antibot", False)
            await ctx.send(embed=embeds.info(t(ctx, "antibot.off")))
        else:
            await ctx.send(embed=embeds.error(
                t(ctx, "toggle.usage", name="antibot")))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if not member.bot:
            return
        if not storage.get_setting(member.guild.id, "antibot", False):
            return
        try:
            await member.kick(reason="Anti-bot activé")
            log.info("Bot %s expulsé de %s (anti-bot)", member, member.guild.name)
        except discord.HTTPException:
            log.warning("Échec de l'expulsion du bot %s", member)
            return
        await self._log_kick(member)

    async def _log_kick(self, member: discord.Member) -> None:
        """Consigne l'expulsion anti-bot dans le salon de logs « mod »."""
        channel = logchannels.log_channel(member.guild, "mod")
        if channel is None:
            return
        embed = discord.Embed(
            title=t(member.guild, "antibot.log_title"),
            description=t(member.guild, "antibot.log_desc",
                          user=f"{member} (`{member.id}`)"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiBot(bot))
