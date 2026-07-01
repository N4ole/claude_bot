"""Commande owner `reload` : recharge un cog à chaud (ou tous)."""
import discord
from discord.ext import commands

import checks


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

    @commands.hybrid_command(
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
            desc = f"✅ Rechargés : {len(reloaded)}"
            if failed:
                desc += "\n❌ Échecs :\n" + "\n".join(failed)
            await ctx.send(desc)
            return

        extension = self._match_extension(cog)
        if extension is None:
            await ctx.send(f"❌ Cog introuvable : `{cog}`")
            return

        try:
            await self.bot.reload_extension(extension)
            await self.bot.tree.sync()
            await ctx.send(f"✅ Cog rechargé : `{extension}`")
        except Exception as exc:  # noqa: BLE001
            await ctx.send(f"❌ Échec du rechargement de `{extension}` : {exc}")

    @reload.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Cette commande est réservée aux owners du bot.")
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reload(bot))
