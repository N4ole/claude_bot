"""Commande admin `protections` : état de toutes les protections du serveur."""
import discord
from discord.ext import commands

from utils import storage
from utils.i18n import t

# Protections activables via commande (clé de réglage -> clé de libellé i18n).
_TOGGLES = {
    "antibot": "prot.antibot",
    "antiraid": "prot.antiraid",
    "antipub": "prot.antipub",
    "antispam": "prot.antispam",
    "antiinsulte": "prot.antiinsulte",
}


class Protections(commands.Cog):
    """Vue d'ensemble des protections du serveur."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="protections",
        description="Affiche l'état des protections du serveur.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def protections(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title=t(ctx, "prot.title"),
            color=discord.Color.blurple(),
        )

        lines = []
        for key, label_key in _TOGGLES.items():
            active = storage.get_setting(ctx.guild.id, key, False)
            state = t(ctx, "prot.on") if active else t(ctx, "prot.off")
            lines.append(f"{t(ctx, label_key)} : **{state}**")
        embed.add_field(
            name=t(ctx, "prot.toggleable"), value="\n".join(lines), inline=False
        )

        embed.add_field(
            name=t(ctx, "prot.always"),
            value=t(ctx, "prot.always_val"),
            inline=False,
        )
        embed.set_footer(text=t(ctx, "prot.footer"))
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Protections(bot))
