"""Commandes `mutemicro` / `unmutemicro` : coupe/rend le micro en vocal.

Applique un « server mute » Discord : le membre garde son casque mais ne peut
plus parler. Le membre doit être connecté à un salon vocal.
"""
import discord
from discord.ext import commands

from utils import checks, embeds, storage
from utils.i18n import t


class VoiceMute(commands.Cog):
    """Mute micro d'un membre en vocal (permission « Rendre muet »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="mutemicro",
        description="Coupe le micro d'un membre en vocal (server mute).",
    )
    @checks.mute_voice_perms()
    async def mutemicro(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if not checks.can_act_on(ctx.author, member):
            await ctx.send(embed=embeds.error(t(ctx, "voice.hierarchy")))
            return
        if member.voice is None or member.voice.channel is None:
            await ctx.send(embed=embeds.error(
                t(ctx, "voice.not_connected", user=member.mention)))
            return
        if member.voice.mute:
            await ctx.send(embed=embeds.warn(
                t(ctx, "voice.already_mic_muted", user=member.mention)))
            return
        try:
            await member.edit(mute=True, reason=f"Mute micro par {ctx.author}")
        except discord.Forbidden:
            await ctx.send(embed=embeds.error(t(ctx, "voice.forbidden")))
            return
        except discord.HTTPException as exc:
            await ctx.send(embed=embeds.error(t(ctx, "voice.failed", error=exc)))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vmute", ctx.author.id)
        await ctx.send(embed=embeds.success(
            t(ctx, "voice.mic_muted", user=member.mention)))

    @commands.hybrid_command(
        name="unmutemicro",
        description="Rend le micro à un membre en vocal.",
    )
    @checks.mute_voice_perms()
    async def unmutemicro(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        if member.voice is None or member.voice.channel is None:
            await ctx.send(embed=embeds.error(
                t(ctx, "voice.not_connected", user=member.mention)))
            return
        if not member.voice.mute:
            await ctx.send(embed=embeds.warn(
                t(ctx, "voice.not_mic_muted", user=member.mention)))
            return
        try:
            await member.edit(mute=False, reason=f"Unmute micro par {ctx.author}")
        except discord.HTTPException as exc:
            await ctx.send(embed=embeds.error(t(ctx, "voice.failed", error=exc)))
            return
        storage.add_modlog(ctx.guild.id, member.id, "vunmute", ctx.author.id)
        await ctx.send(embed=embeds.success(
            t(ctx, "voice.mic_unmuted", user=member.mention)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceMute(bot))
