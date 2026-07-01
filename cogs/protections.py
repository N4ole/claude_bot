"""Commande admin `protections` : état de toutes les protections du serveur."""
import discord
from discord.ext import commands

from utils import storage

# Protections activables via commande (clé de réglage -> libellé).
_TOGGLES = {
    "antibot": "🤖 Anti-bot",
    "antiraid": "🛡️ Anti-raid (captcha)",
    "antipub": "🚫 Anti-pub (invitations)",
    "antispam": "⏱️ Anti-spam",
    "antiinsulte": "🤬 Anti-insulte",
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
            title="🛡️ Protections du serveur",
            color=discord.Color.blurple(),
        )

        lines = []
        for key, label in _TOGGLES.items():
            active = storage.get_setting(ctx.guild.id, key, False)
            state = "🟢 Activé" if active else "🔴 Désactivé"
            lines.append(f"{label} : **{state}**")
        embed.add_field(
            name="Activables", value="\n".join(lines), inline=False
        )

        # Automodération toujours active.
        embed.add_field(
            name="Toujours actives",
            value=(
                "🔠 Anti-majuscules : **🟢**\n"
                "😀 Anti-emojis : **🟢**"
            ),
            inline=False,
        )
        embed.set_footer(
            text="Active/désactive : antibot, antiraid, antipub, antispam <on/off>"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Protections(bot))
