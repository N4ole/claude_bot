"""Commande `contactowner` : le propriétaire d'un serveur contacte les owners.

Réservée au propriétaire du serveur Discord. Envoie en message privé à tous
les owners du bot le message fourni, accompagné des informations du serveur
et d'une invitation vers celui-ci.
"""
import discord
from discord.ext import commands

import config
import storage


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
        ids = list(storage.get_owners())
        if config.OWNER_ID is not None and config.OWNER_ID not in ids:
            ids.insert(0, config.OWNER_ID)
        return ids

    @commands.hybrid_command(
        name="contactowner",
        description="Contacte les owners du bot (réservé au propriétaire du serveur).",
    )
    @commands.guild_only()
    async def contactowner(
        self, ctx: commands.Context, *, message: str
    ) -> None:
        guild = ctx.guild

        # Réservé au propriétaire du serveur Discord.
        if ctx.author.id != guild.owner_id:
            await ctx.send(
                "⛔ Seul le propriétaire du serveur peut utiliser cette commande."
            )
            return

        invite_url = await self._create_invite(guild)

        embed = discord.Embed(
            title="📨 Message d'un propriétaire de serveur",
            description=message,
            color=discord.Color.gold(),
        )
        embed.add_field(name="Serveur", value=guild.name, inline=True)
        embed.add_field(name="ID serveur", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Membres", value=str(guild.member_count), inline=True
        )
        embed.add_field(
            name="Propriétaire",
            value=f"{ctx.author} (`{ctx.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name="Invitation",
            value=invite_url or "*(impossible de créer une invitation)*",
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
            await ctx.send(
                f"✅ Ton message a été transmis à {sent} owner(s) du bot."
            )
        else:
            await ctx.send(
                "❌ Impossible de contacter les owners du bot pour le moment."
            )

    @contactowner.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage : `contactowner <message>`.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Cette commande s'utilise sur un serveur.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ContactOwner(bot))
