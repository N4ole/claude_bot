"""Commande owner `central` : tableau de bord global du bot."""
from datetime import datetime, timezone

import discord
from discord.ext import commands

import config
from utils import checks, storage
from utils.duration import human
from utils.i18n import t

_PROTECTIONS = {
    "antibot": "prot.antibot",
    "antiraid": "prot.antiraid",
    "antipub": "prot.antipub",
    "antispam": "prot.antispam",
    "antiinsulte": "prot.antiinsulte",
}


class Central(commands.Cog):
    """Centralisation des statistiques du bot (owners)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="central",
        description="Tableau de bord global du bot (owners).",
    )
    @checks.is_owner()
    async def central(self, ctx: commands.Context) -> None:
        guilds = self.bot.guilds

        # Membres.
        total_members = sum((g.member_count or 0) for g in guilds)
        bots = sum(1 for g in guilds for m in g.members if m.bot)
        humans = total_members - bots

        # Mutes (timeouts actifs) et confinements (salons confin-*).
        now = datetime.now(timezone.utc)
        muted = 0
        confined = 0
        for g in guilds:
            for m in g.members:
                if m.timed_out_until and m.timed_out_until > now:
                    muted += 1
            category = discord.utils.get(g.categories, name="confinement")
            if category:
                confined += sum(
                    1 for c in category.text_channels
                    if c.name.startswith("confin-")
                )

        watched = storage.total_watched()
        warned_users, warn_points = storage.warn_totals()
        reminders = len(storage.get_reminders())
        timed_confinements = len(storage.get_confinements())
        owners = len(storage.get_owners()) + (1 if config.OWNER_ID else 0)
        uptime = human(now - self.bot.start_time)

        embed = discord.Embed(
            title=t(ctx, "central.title"),
            color=discord.Color.gold(),
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name=t(ctx, "central.servers"),
            value=t(ctx, "central.servers_val", guilds=len(guilds),
                    members=total_members, humans=humans, bots=bots),
            inline=True,
        )
        embed.add_field(
            name=t(ctx, "central.mod"),
            value=t(ctx, "central.mod_val", muted=muted, confined=confined,
                    watched=watched),
            inline=True,
        )
        embed.add_field(
            name=t(ctx, "central.warns"),
            value=t(ctx, "central.warns_val", users=warned_users,
                    points=warn_points, timed=timed_confinements),
            inline=True,
        )

        prot = "\n".join(
            t(ctx, "central.prot_line", label=t(ctx, label_key),
              count=storage.count_setting_enabled(key))
            for key, label_key in _PROTECTIONS.items()
        )
        embed.add_field(name=t(ctx, "central.prot"), value=prot, inline=False)

        embed.add_field(name=t(ctx, "central.reminders"),
                        value=str(reminders), inline=True)
        embed.add_field(name=t(ctx, "central.owners"),
                        value=str(owners), inline=True)
        embed.add_field(
            name=t(ctx, "central.bot"),
            value=t(ctx, "central.bot_val",
                    version=(f"{config.VERSION} {t(ctx, 'bi.beta')}"
                             if config.BETA else config.VERSION),
                    ping=round(self.bot.latency * 1000), uptime=uptime),
            inline=True,
        )
        await ctx.send(embed=embed)

    @central.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Central(bot))
