"""Commande `userinfo` : affiche toutes les informations d'un utilisateur."""
import discord
from discord.ext import commands

_STATUS_LABELS = {
    discord.Status.online: "🟢 En ligne",
    discord.Status.idle: "🌙 Absent",
    discord.Status.dnd: "⛔ Ne pas déranger",
    discord.Status.offline: "⚫ Hors ligne",
}


class UserInfo(commands.Cog):
    """Informations détaillées sur un utilisateur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Affiche les informations d'un utilisateur.",
    )
    @commands.guild_only()
    async def userinfo(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        member = member or ctx.author
        # Un membre résolu via une commande slash ne porte pas la présence :
        # on récupère la version en cache pour obtenir le vrai statut.
        member = ctx.guild.get_member(member.id) or member

        embed = discord.Embed(
            title=f"Informations sur {member}",
            color=member.color if member.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Identité.
        embed.add_field(name="Nom", value=str(member), inline=True)
        embed.add_field(name="Surnom", value=member.nick or "*(aucun)*", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Bot", value="Oui" if member.bot else "Non", inline=True)

        # Statut et activité.
        status = _STATUS_LABELS.get(member.status, str(member.status))
        embed.add_field(name="Statut", value=status, inline=True)
        if member.activity is not None:
            embed.add_field(
                name="Activité", value=str(member.activity.name), inline=True
            )

        # Dates.
        embed.add_field(
            name="Compte créé",
            value=discord.utils.format_dt(member.created_at, style="F"),
            inline=False,
        )
        if member.joined_at is not None:
            embed.add_field(
                name="A rejoint le serveur",
                value=discord.utils.format_dt(member.joined_at, style="F"),
                inline=False,
            )
        if member.premium_since is not None:
            embed.add_field(
                name="Booste depuis",
                value=discord.utils.format_dt(member.premium_since, style="F"),
                inline=False,
            )

        # Rôles (hors @everyone).
        roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        embed.add_field(
            name=f"Rôles ({len(roles)})",
            value=", ".join(roles) if roles else "*(aucun)*",
            inline=False,
        )
        embed.add_field(
            name="Rôle le plus haut", value=member.top_role.mention, inline=True
        )

        embed.set_footer(text=f"Demandé par {ctx.author}")
        await ctx.send(embed=embed)

    @userinfo.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Utilisateur introuvable.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserInfo(bot))
