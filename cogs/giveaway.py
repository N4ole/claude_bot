"""Système de giveaways : `giveaway`, `gend`, `greroll` (admins).

Un giveaway est un message avec une réaction 🎉 : les membres y réagissent pour
participer. À l'échéance, le bot tire au sort le(s) gagnant(s) parmi les
participants. Les giveaways en cours sont persistés et repris au démarrage.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils import checks, storage
from utils.duration import human, parse_duration
from utils.i18n import t

log = logging.getLogger(__name__)

EMOJI = "🎉"
MAX_WINNERS = 20


class Giveaway(commands.Cog):
    """Création et tirage de giveaways (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._resumed = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Reprend les giveaways en cours après un redémarrage (une fois)."""
        if self._resumed:
            return
        self._resumed = True
        for gw in storage.get_active_giveaways():
            self.bot.loop.create_task(self._schedule_end(gw["message_id"]))

    # ------------------------------------------------------------------ #
    # Planification / tirage
    # ------------------------------------------------------------------ #
    async def _schedule_end(self, message_id: int) -> None:
        gw = storage.get_giveaway(message_id)
        if gw is None or gw.get("ended"):
            return
        delay = gw["end"] - datetime.now(timezone.utc).timestamp()
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        await self._end_giveaway(message_id)

    async def _fetch_message(self, gw: dict) -> discord.Message | None:
        channel = self.bot.get_channel(gw["channel_id"])
        if channel is None or not hasattr(channel, "fetch_message"):
            return None
        try:
            return await channel.fetch_message(gw["message_id"])
        except (discord.NotFound, discord.HTTPException):
            return None

    async def _participants(self, message: discord.Message) -> list[discord.Member]:
        """Liste des membres (hors bots) ayant réagi 🎉 au giveaway."""
        reaction = discord.utils.get(message.reactions, emoji=EMOJI)
        if reaction is None:
            return []
        users = []
        async for user in reaction.users():
            if not user.bot:
                users.append(user)
        return users

    async def _end_giveaway(self, message_id: int) -> None:
        gw = storage.get_giveaway(message_id)
        if gw is None or gw.get("ended"):
            return
        storage.mark_giveaway_ended(message_id)
        message = await self._fetch_message(gw)
        if message is None:
            # Message/salon disparu : on nettoie.
            storage.remove_giveaway(message_id)
            return

        src = message.guild
        participants = await self._participants(message)
        winners = random.sample(
            participants, min(gw["winners"], len(participants))
        ) if participants else []

        embed = message.embeds[0] if message.embeds else discord.Embed()
        embed.color = discord.Color.dark_grey()
        embed.description = t(src, "gw.ended_desc", prize=gw["prize"])
        if winners:
            won = ", ".join(w.mention for w in winners)
            embed.clear_fields()
            embed.add_field(name=t(src, "gw.winners_field"), value=won,
                            inline=False)
            try:
                await message.edit(embed=embed)
            except discord.HTTPException:
                pass
            await self._announce(message, gw, won)
        else:
            embed.clear_fields()
            embed.add_field(name=t(src, "gw.winners_field"),
                            value=t(src, "gw.no_participant"), inline=False)
            try:
                await message.edit(embed=embed)
            except discord.HTTPException:
                pass
            try:
                await message.reply(t(src, "gw.no_participant"))
            except discord.HTTPException:
                pass

    async def _announce(
        self, message: discord.Message, gw: dict, winners_mention: str
    ) -> None:
        try:
            await message.reply(
                t(message.guild, "gw.announce", winners=winners_mention,
                  prize=gw["prize"], link=message.jump_url)
            )
        except discord.HTTPException:
            pass

    # ------------------------------------------------------------------ #
    # Commandes
    # ------------------------------------------------------------------ #
    @commands.hybrid_command(
        name="giveaway",
        description="Lance un giveaway (ex: giveaway 1h 1 Nitro).",
    )
    @checks.admin()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def giveaway(
        self, ctx: commands.Context, duree: str, gagnants: int, *, prix: str
    ) -> None:
        delta = parse_duration(duree)
        if delta is None:
            await ctx.send(t(ctx, "gw.bad_duration"))
            return
        if gagnants < 1 or gagnants > MAX_WINNERS:
            await ctx.send(t(ctx, "gw.bad_winners", max=MAX_WINNERS))
            return

        end = discord.utils.utcnow() + delta
        embed = discord.Embed(
            title=t(ctx, "gw.title", prize=prix),
            description=t(ctx, "gw.desc", emoji=EMOJI, winners=gagnants),
            color=discord.Color.gold(),
            timestamp=end,
        )
        embed.add_field(name=t(ctx, "gw.ends"),
                        value=discord.utils.format_dt(end, style="R"),
                        inline=True)
        embed.add_field(name=t(ctx, "gw.host"), value=ctx.author.mention,
                        inline=True)
        embed.set_footer(text=t(ctx, "gw.footer", duration=human(delta)))

        message = await ctx.channel.send(embed=embed)
        try:
            await message.add_reaction(EMOJI)
        except discord.HTTPException:
            pass
        storage.add_giveaway(
            message.id, ctx.channel.id, ctx.guild.id, prix, gagnants,
            end.timestamp(), ctx.author.id,
        )
        self.bot.loop.create_task(self._schedule_end(message.id))

        if ctx.interaction is not None:
            await ctx.send(t(ctx, "gw.started", link=message.jump_url),
                           ephemeral=True)

    @commands.hybrid_command(
        name="gend",
        description="Termine immédiatement un giveaway (par ID de message).",
    )
    @checks.admin()
    async def gend(self, ctx: commands.Context, message_id: str) -> None:
        if not message_id.isdigit():
            await ctx.send(t(ctx, "gw.bad_id"))
            return
        mid = int(message_id)
        gw = storage.get_giveaway(mid)
        if gw is None or gw["guild_id"] != ctx.guild.id:
            await ctx.send(t(ctx, "gw.not_found"))
            return
        if gw.get("ended"):
            await ctx.send(t(ctx, "gw.already_ended"))
            return
        await self._end_giveaway(mid)
        await ctx.send(t(ctx, "gw.force_ended"))

    @commands.hybrid_command(
        name="greroll",
        description="Retire un nouveau gagnant d'un giveaway terminé.",
    )
    @checks.admin()
    async def greroll(self, ctx: commands.Context, message_id: str) -> None:
        if not message_id.isdigit():
            await ctx.send(t(ctx, "gw.bad_id"))
            return
        mid = int(message_id)
        gw = storage.get_giveaway(mid)
        if gw is None or gw["guild_id"] != ctx.guild.id:
            await ctx.send(t(ctx, "gw.not_found"))
            return
        if not gw.get("ended"):
            await ctx.send(t(ctx, "gw.not_ended"))
            return
        message = await self._fetch_message(gw)
        if message is None:
            await ctx.send(t(ctx, "gw.msg_gone"))
            return
        participants = await self._participants(message)
        if not participants:
            await ctx.send(t(ctx, "gw.no_participant"))
            return
        winner = random.choice(participants)
        await ctx.send(t(ctx, "gw.reroll", winner=winner.mention,
                         prize=gw["prize"]))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Giveaway(bot))
