"""Commande owner `helpowner` (préfixe uniquement) : liste les commandes owner."""
import discord
from discord.ext import commands

from utils import checks
import config
from utils.i18n import t


class HelpOwner(commands.Cog):
    """Aide dédiée aux commandes d'owner."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _owner_commands(self) -> list[commands.Command]:
        return sorted(
            (
                cmd
                for cmd in self.bot.commands
                if cmd.module and cmd.module.startswith("cogs.owner")
            ),
            key=lambda c: c.qualified_name,
        )

    def _detail(self, ctx, command: commands.Command) -> discord.Embed:
        signature = command.signature.strip()
        usage = f"{config.PREFIX}{command.qualified_name}"
        if signature:
            usage += f" {signature}"
        embed = discord.Embed(
            title=f"👑 {config.PREFIX}{command.qualified_name}",
            description=command.description or command.help
            or t(ctx, "help.no_desc"),
            color=discord.Color.gold(),
        )
        embed.add_field(name=t(ctx, "ho.usage"), value=f"`{usage}`", inline=False)
        embed.add_field(
            name=t(ctx, "ho.avail"),
            value=t(ctx, "ho.avail_both", prefix=config.PREFIX)
            if isinstance(command, commands.HybridCommand)
            else t(ctx, "ho.avail_prefix"),
            inline=True,
        )
        if command.aliases:
            embed.add_field(
                name=t(ctx, "ho.alias"),
                value=", ".join(f"`{a}`" for a in command.aliases),
                inline=True,
            )
        embed.add_field(
            name=t(ctx, "ho.dm"), value=t(ctx, "ho.dm_val"), inline=True,
        )
        embed.set_footer(text=t(ctx, "ho.legend"))
        return embed

    @commands.command(
        name="helpowner",
        description="Liste les commandes réservées aux owners du bot.",
    )
    @checks.is_owner()
    async def helpowner(
        self, ctx: commands.Context, commande: str | None = None
    ) -> None:
        owner_commands = self._owner_commands()

        # Détail d'une commande owner précise.
        if commande:
            name = commande.lower().lstrip(config.PREFIX).strip()
            command = self.bot.get_command(name)
            if command is None or command not in owner_commands:
                await ctx.send(t(ctx, "ho.not_found", cmd=commande))
                return
            await ctx.send(embed=self._detail(ctx, command))
            return

        embed = discord.Embed(
            title=t(ctx, "ho.title"),
            description=t(ctx, "ho.desc", prefix=config.PREFIX),
            color=discord.Color.gold(),
        )
        for cmd in owner_commands:
            description = cmd.description or cmd.help or t(ctx, "help.no_desc")
            signature = cmd.signature.strip()
            usage = f"{config.PREFIX}{cmd.qualified_name}"
            if signature:
                usage += f" {signature}"
            embed.add_field(
                name=f"`{usage}`",
                value=description,
                inline=False,
            )
        embed.set_footer(text=t(ctx, "ho.footer", count=len(owner_commands)))
        await ctx.send(embed=embed)

    @helpowner.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpOwner(bot))
