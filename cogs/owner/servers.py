"""Commande owner `serveurs` : détail de chaque serveur, une page par serveur."""
import discord
from discord.ext import commands

from utils import checks
from utils.i18n import t

_VERIF = {
    discord.VerificationLevel.none: "verif.none",
    discord.VerificationLevel.low: "verif.low",
    discord.VerificationLevel.medium: "verif.medium",
    discord.VerificationLevel.high: "verif.high",
    discord.VerificationLevel.highest: "verif.highest",
}


def _guild_embed(src, guild: discord.Guild, index: int, total: int) -> discord.Embed:
    """Construit l'embed détaillé d'un serveur (traduit selon `src`)."""
    bots = sum(1 for m in guild.members if m.bot)
    humans = (guild.member_count or 0) - bots

    embed = discord.Embed(
        title=guild.name,
        description=guild.description or None,
        color=discord.Color.blurple(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.add_field(name=t(src, "f.id"), value=f"`{guild.id}`", inline=True)
    embed.add_field(
        name=t(src, "f.owner"),
        value=f"{guild.owner} (`{guild.owner_id}`)" if guild.owner
        else f"`{guild.owner_id}`",
        inline=True,
    )
    embed.add_field(
        name=t(src, "f.created"),
        value=discord.utils.format_dt(guild.created_at, style="D"),
        inline=True,
    )

    embed.add_field(
        name=t(src, "f.members"),
        value=t(src, "srv.members_val", count=guild.member_count,
                humans=humans, bots=bots),
        inline=True,
    )
    embed.add_field(
        name=t(src, "srv.channels"),
        value=(
            f"💬 {len(guild.text_channels)} · 🔊 {len(guild.voice_channels)}\n"
            f"📁 {len(guild.categories)} · 🎙️ {len(guild.stage_channels)} · "
            f"📑 {len(guild.forums)}"
        ),
        inline=True,
    )
    embed.add_field(
        name=t(src, "srv.roles_emojis"),
        value=t(src, "srv.roles_val", roles=len(guild.roles),
                emojis=len(guild.emojis), emoji_lim=guild.emoji_limit,
                stickers=len(guild.stickers), sticker_lim=guild.sticker_limit),
        inline=True,
    )

    embed.add_field(
        name=t(src, "f.boosts"),
        value=t(src, "si.boosts_val", count=guild.premium_subscription_count,
                tier=guild.premium_tier),
        inline=True,
    )
    embed.add_field(
        name=t(src, "srv.verif"),
        value=t(src, _VERIF.get(guild.verification_level, "verif.none")),
        inline=True,
    )
    joined = guild.me.joined_at if guild.me else None
    embed.add_field(
        name=t(src, "srv.bot_since"),
        value=discord.utils.format_dt(joined, style="R") if joined else "?",
        inline=True,
    )

    # Salon système, AFK, langue.
    extras = []
    if guild.system_channel:
        extras.append(t(src, "srv.sys_channel",
                        channel=guild.system_channel.mention))
    if guild.afk_channel:
        extras.append(t(src, "srv.afk", channel=guild.afk_channel.name,
                        minutes=guild.afk_timeout // 60))
    extras.append(t(src, "srv.locale", locale=guild.preferred_locale))
    if guild.vanity_url_code:
        extras.append(t(src, "srv.vanity", code=guild.vanity_url_code))
    embed.add_field(name=t(src, "srv.misc"), value="\n".join(extras),
                    inline=False)

    if guild.features:
        embed.add_field(
            name=t(src, "srv.features"),
            value=", ".join(f"`{f.lower()}`" for f in guild.features)[:1000],
            inline=False,
        )

    embed.set_footer(
        text=t(src, "srv.footer", index=index + 1, total=total)
    )
    return embed


class ServersView(discord.ui.View):
    """Navigation entre les serveurs (une page par serveur)."""

    def __init__(
        self, guilds: list[discord.Guild], author_id: int, source
    ) -> None:
        # Délai réarmé à chaque clic (inactivité) ; large pour la navigation.
        super().__init__(timeout=600)
        self.guilds = guilds
        self.index = 0
        self.author_id = author_id
        self.source = source
        self.message: discord.Message | None = None
        self._refresh()

    def _refresh(self) -> None:
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.guilds) - 1
        self.counter.label = f"{self.index + 1}/{len(self.guilds)}"

    def current_embed(self) -> discord.Embed:
        return _guild_embed(
            self.source, self.guilds[self.index], self.index, len(self.guilds)
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                t(self.source, "help.not_for_you"), ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:
        self.index = max(0, self.index - 1)
        self._refresh()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.primary, disabled=True)
    async def counter(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:  # pragma: no cover
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(
        self, interaction: discord.Interaction, _b: discord.ui.Button
    ) -> None:
        self.index = min(len(self.guilds) - 1, self.index + 1)
        self._refresh()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)


class Servers(commands.Cog):
    """Détail des serveurs du bot (owners)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="serveurs",
        description="Détaille chaque serveur du bot (une page par serveur).",
    )
    @checks.is_owner()
    async def serveurs(self, ctx: commands.Context) -> None:
        guilds = sorted(
            self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True
        )
        if not guilds:
            await ctx.send(t(ctx, "srv.none"))
            return
        view = ServersView(guilds, ctx.author.id, ctx.guild)
        view.message = await ctx.send(embed=view.current_embed(), view=view)

    @serveurs.error
    async def _error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.send(t(ctx, "error.owner_only"))
        else:
            # Repli : jamais d'erreur silencieuse pour l'utilisateur
            # (errorreport prévient déjà les owners avec la traceback).
            await ctx.send(t(ctx, "error.generic"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Servers(bot))
