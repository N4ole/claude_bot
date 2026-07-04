"""Commande `contactowner` : le propriétaire d'un serveur contacte les owners.

Réservée au propriétaire du serveur Discord. Envoie en message privé à tous
les owners du bot le message fourni, accompagné des informations du serveur
et d'une invitation vers celui-ci.
"""
import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t


class ContactOwner(commands.Cog):
    """Permet au propriétaire d'un serveur de contacter les owners du bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _create_invite(self, guild: discord.Guild) -> str | None:
        """Crée une invitation permanente vers le serveur, si possible."""
        channel = next(
            (
                c
                for c in guild.text_channels
                if c.permissions_for(guild.me).create_instant_invite
            ),
            None,
        )
        if channel is None:
            return None
        try:
            invite = await channel.create_invite(
                max_age=0, max_uses=0, unique=True,
                reason="contactowner",
            )
            return invite.url
        except discord.HTTPException:
            return None

    def _bot_owner_ids(self) -> list[int]:
        return checks.all_owner_ids()

    @commands.hybrid_command(
        name="contactowner",
        description="Contacte les owners du bot (réservé au propriétaire du serveur).",
    )
    @checks.server_owner()
    async def contactowner(
        self, ctx: commands.Context, *, message: str
    ) -> None:
        guild = ctx.guild
        invite_url = await self._create_invite(guild)

        embed = discord.Embed(
            title=t(ctx, "co.title"),
            description=message,
            color=discord.Color.gold(),
        )
        embed.add_field(name=t(ctx, "co.server"), value=guild.name, inline=True)
        embed.add_field(name=t(ctx, "co.server_id"), value=f"`{guild.id}`",
                        inline=True)
        embed.add_field(
            name=t(ctx, "f.members"), value=str(guild.member_count), inline=True
        )
        embed.add_field(
            name=t(ctx, "co.owner"),
            value=f"{ctx.author} (`{ctx.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name=t(ctx, "co.invite"),
            value=invite_url or t(ctx, "co.no_invite"),
            inline=False,
        )
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)

        # Envoi du MP à chaque owner du bot.
        sent, failed = 0, 0
        for owner_id in self._bot_owner_ids():
            try:
                user = self.bot.get_user(owner_id) or await self.bot.fetch_user(
                    owner_id
                )
                await user.send(embed=embed)
                sent += 1
            except (discord.HTTPException, discord.NotFound):
                failed += 1

        if sent:
            await ctx.send(t(ctx, "co.sent", count=sent))
        else:
            await ctx.send(t(ctx, "co.failed"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ContactOwner(bot))
