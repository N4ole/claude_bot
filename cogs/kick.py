"""Commande admin `kick` : expulse un utilisateur du serveur, avec raison."""
import logging

import discord
from discord.ext import commands

from utils import storage
from utils.i18n import t

log = logging.getLogger("action")


class Kick(commands.Cog):
    """Expulsion d'utilisateurs (permission « Expulser des membres »)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Expulse un utilisateur du serveur (avec raison).",
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self, ctx: commands.Context, member: discord.Member,
        *, raison: str | None = None,
    ) -> None:
        reason = raison or t(ctx, "mod.no_reason")

        # Garde-fous : soi-même et hiérarchie des rôles.
        if member.id == ctx.author.id:
            await ctx.send(t(ctx, "kick.self"))
            return
        if (
            ctx.author.id != ctx.guild.owner_id
            and member.top_role >= ctx.author.top_role
        ):
            await ctx.send(t(ctx, "kick.hierarchy"))
            return

        # Prévenir l'utilisateur en MP AVANT l'expulsion (après, le bot ne
        # partage plus forcément de serveur avec lui). Sans invitation.
        dm = discord.Embed(
            title=t(member, "kick.dm_title"),
            description=t(member, "kick.dm_desc", server=ctx.guild.name),
            color=discord.Color.orange(),
        )
        dm.add_field(name=t(member, "mod.reason_label"), value=reason,
                     inline=False)
        dm_sent = True
        try:
            await member.send(embed=dm)
        except (discord.HTTPException, discord.Forbidden):
            dm_sent = False  # MP fermés : on expulse quand même.

        try:
            await member.kick(reason=f"{ctx.author} : {reason}")
        except discord.Forbidden:
            await ctx.send(t(ctx, "kick.forbidden"))
            return
        except discord.HTTPException as exc:
            await ctx.send(t(ctx, "kick.failed", error=exc))
            return

        storage.add_modlog(
            ctx.guild.id, member.id, "kick", ctx.author.id, detail=reason
        )
        log.info(
            "Kick — %s (%s) expulsé par %s (%s) sur %s (%s) : %s",
            member, member.id, ctx.author, ctx.author.id,
            ctx.guild.name, ctx.guild.id, reason,
        )
        confirm = t(ctx, "kick.done", user=str(member), reason=reason)
        if not dm_sent:
            confirm += f"\n{t(ctx, 'mod.dm_failed')}"
        await ctx.send(confirm)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
