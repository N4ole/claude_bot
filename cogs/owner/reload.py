"""Commande owner `reload` : recharge un cog à chaud (ou tous)."""
import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t


class Reload(commands.Cog):
    """Rechargement à chaud des cogs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _match_extension(self, name: str) -> str | None:
        """Trouve l'extension chargée correspondant à un nom court."""
        if name in self.bot.extensions:
            return name
        for ext in self.bot.extensions:
            # Match sur le dernier segment (ex: "ping" -> "cogs.ping").
            if ext.split(".")[-1] == name:
                return ext
        return None

    @commands.command(
        name="reload",
        description="Recharge un cog à chaud (ou 'all' pour tout recharger).",
    )
    @checks.is_owner()
    async def reload(self, ctx: commands.Context, cog: str = "all") -> None:
        if cog == "all":
            reloaded, failed = [], []
            for ext in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(ext)
                    reloaded.append(ext)
                except Exception as exc:  # noqa: BLE001
                    failed.append(f"{ext} ({exc})")
            await self.bot.tree.sync()
            desc = t(ctx, "reload.all_ok", count=len(reloaded))
            if failed:
                desc += t(ctx, "reload.all_fail", failed="\n".join(failed))
            await ctx.send(desc)
            return

        extension = self._match_extension(cog)
        if extension is None:
            await ctx.send(t(ctx, "reload.not_found", cog=cog))
            return

        try:
            await self.bot.reload_extension(extension)
            await self.bot.tree.sync()
            await ctx.send(t(ctx, "reload.one", cog=extension))
        except Exception as exc:  # noqa: BLE001
            await ctx.send(t(ctx, "reload.one_fail", cog=extension, error=exc))

    @reload.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reload(bot))
