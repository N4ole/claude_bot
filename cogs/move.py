"""Commande `move` : déplace un membre vers un autre salon vocal."""
import discord
from discord.ext import commands

from utils import checks, storage
from utils.i18n import t


class Move(commands.Cog):
    """Déplacement vocal d'un membre (permission « Déplacer des membres »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="move",
        description="Déplace un membre vers un autre salon vocal.",
    )
    @checks.move_perms()
    async def move(
        self,
        ctx: commands.Context,
        member: discord.Member,
        salon: discord.VoiceChannel,
    ) -> None:
        if not checks.can_act_on(ctx.author, member):
            await ctx.send(t(ctx, "voice.hierarchy"))
            return
        if member.voice is None or member.voice.channel is None:
            await ctx.send(t(ctx, "voice.not_connected", user=member.mention))
            return
        if member.voice.channel.id == salon.id:
            await ctx.send(
                t(ctx, "move.already_there", user=member.mention,
                  channel=salon.mention)
            )
            return
        try:
            await member.move_to(salon, reason=f"Déplacé par {ctx.author}")
        except discord.Forbidden:
            await ctx.send(t(ctx, "voice.forbidden"))
            return
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "voice.failed", error=exc))
            return
        storage.add_modlog(
            ctx.guild.id, member.id, "move", ctx.author.id, detail=salon.name
        )
        await ctx.send(
            t(ctx, "move.done", user=member.mention, channel=salon.mention)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Move(bot))
