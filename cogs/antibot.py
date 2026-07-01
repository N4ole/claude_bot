"""Commande admin `antibot on/off` : empêche les bots de rejoindre le serveur."""
import logging

import discord
from discord.ext import commands

from utils import storage

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
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def antibot(self, ctx: commands.Context, etat: str) -> None:
        value = etat.lower()
        if value in _ON:
            storage.set_setting(ctx.guild.id, "antibot", True)
            await ctx.send(
                "🤖 **Anti-bot activé** : les bots qui rejoignent seront "
                "automatiquement expulsés."
            )
        elif value in _OFF:
            storage.set_setting(ctx.guild.id, "antibot", False)
            await ctx.send("🤖 **Anti-bot désactivé**.")
        else:
            await ctx.send("❌ Utilise `antibot on` ou `antibot off`.")

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiBot(bot))
