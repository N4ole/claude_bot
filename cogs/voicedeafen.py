"""Commandes `mutecasque` / `unmutecasque` : coupe/rend le son en vocal.

Applique un « server deafen » Discord : le membre n'entend plus le vocal (et
ne peut plus parler tant qu'il est sourd). Le membre doit être connecté à un
salon vocal.
"""
import discord
from discord.ext import commands

from utils import checks, storage
from utils.i18n import t


class VoiceDeafen(commands.Cog):
    """Mute casque d'un membre en vocal (permission « Rendre sourd »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mutecasque",
        description="Coupe le son d'un membre en vocal (server deafen).",
    )
    @checks.deafen_voice_perms()
    async def mutecasque(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if not checks.can_act_on(ctx.author, member):
            await ctx.send(t(ctx, "voice.hierarchy"))
            return
        if member.voice is None or member.voice.channel is None:
            await ctx.send(t(ctx, "voice.not_connected", user=member.mention))
            return
        if member.voice.deaf:
            await ctx.send(t(ctx, "voice.already_deafened", user=member.mention))
            return
        try:
            await member.edit(deafen=True, reason=f"Mute casque par {ctx.author}")
        except discord.Forbidden:
            await ctx.send(t(ctx, "voice.forbidden"))
            return
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "voice.failed", error=exc))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vdeafen", ctx.author.id)
        await ctx.send(t(ctx, "voice.deafened", user=member.mention))

    @commands.hybrid_command(
        name="unmutecasque",
        description="Rend le son à un membre en vocal.",
    )
    @checks.deafen_voice_perms()
    async def unmutecasque(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if member.voice is None or member.voice.channel is None:
            await ctx.send(t(ctx, "voice.not_connected", user=member.mention))
            return
        if not member.voice.deaf:
            await ctx.send(t(ctx, "voice.not_deafened", user=member.mention))
            return
        try:
            await member.edit(deafen=False, reason=f"Unmute casque par {ctx.author}")
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "voice.failed", error=exc))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vundeafen", ctx.author.id)
        await ctx.send(t(ctx, "voice.undeafened", user=member.mention))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceDeafen(bot))
