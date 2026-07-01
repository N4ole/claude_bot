"""Commande help : une page par catégorie, navigation par boutons."""
import discord
from discord.ext import commands

import config

# Catégorie et permission requise, par nom de cog.
_CATEGORIES = {
    # 📊 Infos
    "UserInfo": ("📊 Infos", None),
    "Avatar": ("📊 Infos", None),
    "ServerInfo": ("📊 Infos", None),
    "BotInfo": ("📊 Infos", None),
    "MemberCount": ("📊 Infos", None),
    # 🎲 Utilitaire
    "Poll": ("🎲 Utilitaire", None),
    "Roll": ("🎲 Utilitaire", None),
    "CoinFlip": ("🎲 Utilitaire", None),
    "EightBall": ("🎲 Utilitaire", None),
    "Choose": ("🎲 Utilitaire", None),
    "RemindMe": ("🎲 Utilitaire", None),
    # 🛡️ Modération
    "Watch": ("🛡️ Modération", "Administrateur"),
    "Confine": ("🛡️ Modération", "Administrateur"),
    "Mute": ("🛡️ Modération", "Administrateur"),
    "Warn": ("🛡️ Modération", "Administrateur"),
    "Clear": ("🛡️ Modération", "Gérer les messages"),
    "AntiBot": ("🛡️ Modération", "Administrateur"),
    "AntiRaid": ("🛡️ Modération", "Administrateur"),
    "AntiPub": ("🛡️ Modération", "Administrateur"),
    "AntiSpam": ("🛡️ Modération", "Administrateur"),
    "AntiInsulte": ("🛡️ Modération", "Administrateur"),
    "Protections": ("🛡️ Modération", "Administrateur"),
    "UserStatus": ("🛡️ Modération", "Administrateur"),
    "Analyse": ("🛡️ Modération", "Administrateur"),
    # 👑 Propriétaire
    "ContactOwner": ("👑 Propriétaire de serveur", "Propriétaire du serveur"),
}
_DEFAULT = ("🔧 Général", None)
_ORDER = [
    "🔧 Général", "📊 Infos", "🎲 Utilitaire",
    "🛡️ Modération", "👑 Propriétaire de serveur",
]


class HelpView(discord.ui.View):
    """Vue de navigation entre les pages d'aide."""

    def __init__(self, pages: list[discord.Embed], author_id: int) -> None:
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0
        self.author_id = author_id
        self._refresh()

    def _refresh(self) -> None:
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.pages) - 1
        self.counter.label = f"{self.index + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Ce menu n'est pas pour toi.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        self.index = max(0, self.index - 1)
        self._refresh()
        await interaction.response.edit_message(
            embed=self.pages[self.index], view=self
        )

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.primary, disabled=True)
    async def counter(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:  # pragma: no cover - bouton non cliquable
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        self.index = min(len(self.pages) - 1, self.index + 1)
        self._refresh()
        await interaction.response.edit_message(
            embed=self.pages[self.index], view=self
        )


class Help(commands.Cog):
    """Affiche l'aide, une page par catégorie."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _category_of(self, command: commands.Command) -> tuple[str, str | None]:
        cog_name = command.cog.qualified_name if command.cog else ""
        return _CATEGORIES.get(cog_name, _DEFAULT)

    def _is_hidden(self, command: commands.Command) -> bool:
        """True si la commande ne doit pas apparaître dans l'aide publique."""
        if command.hidden:
            return True
        return bool(command.module and command.module.startswith("cogs.owner"))

    def _command_detail(self, command: commands.Command) -> discord.Embed:
        category, perm = self._category_of(command)
        embed = discord.Embed(
            title=f"Commande : {config.PREFIX}{command.qualified_name}",
            description=command.description or command.help or "Pas de description.",
            color=discord.Color.blurple(),
        )
        signature = command.signature.strip()
        usage = f"{config.PREFIX}{command.qualified_name}"
        if signature:
            usage += f" {signature}"
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        embed.add_field(name="Catégorie", value=category, inline=True)
        embed.add_field(
            name="Permission", value=f"🔒 {perm}" if perm else "Aucune", inline=True
        )
        embed.add_field(
            name="Disponible en",
            value="préfixe `" + config.PREFIX + "` et slash `/`"
            if isinstance(command, commands.HybridCommand)
            else "préfixe uniquement",
            inline=True,
        )
        if command.aliases:
            embed.add_field(
                name="Alias",
                value=", ".join(f"`{a}`" for a in command.aliases),
                inline=False,
            )
        embed.set_footer(
            text="⟨ ⟩ = obligatoire · [ ] = facultatif · "
            f"{config.PREFIX}help pour la liste complète"
        )
        return embed

    def _build_pages(self) -> list[discord.Embed]:
        grouped: dict[str, list[str]] = {}
        total = 0
        for command in sorted(self.bot.commands, key=lambda c: c.name):
            if self._is_hidden(command):
                continue
            category, perm = self._category_of(command)
            desc = command.description or "Pas de description."
            line = f"`{config.PREFIX}{command.name}` — {desc}"
            if perm:
                line += f" 🔒 *{perm}*"
            grouped.setdefault(category, []).append(line)
            total += 1

        ordered = _ORDER + [c for c in grouped if c not in _ORDER]
        pages = []
        page_categories = [c for c in ordered if c in grouped]
        for i, category in enumerate(page_categories):
            embed = discord.Embed(
                title=f"📖 Aide — {category}",
                description=(
                    f"Préfixe `{config.PREFIX}` · aussi en slash `/` · "
                    "🔒 = permission requise."
                ),
                color=discord.Color.blurple(),
            )
            embed.add_field(
                name=category, value="\n".join(grouped[category]), inline=False
            )
            embed.set_footer(
                text=f"Page {i + 1}/{len(page_categories)} · "
                f"{total} commande(s) au total"
            )
            pages.append(embed)
        return pages

    @commands.hybrid_command(
        name="help",
        description="Aide générale, ou détail d'une commande : help [commande].",
    )
    async def help(
        self, ctx: commands.Context, commande: str | None = None
    ) -> None:
        # Détail d'une commande précise.
        if commande:
            name = commande.lower().lstrip(config.PREFIX).strip()
            command = self.bot.get_command(name)
            if command is None or self._is_hidden(command):
                await ctx.send(f"❌ Commande introuvable : `{commande}`")
                return
            await ctx.send(embed=self._command_detail(command))
            return

        # Aide générale paginée.
        pages = self._build_pages()
        if not pages:
            await ctx.send("Aucune commande disponible.")
            return
        view = HelpView(pages, ctx.author.id)
        await ctx.send(embed=pages[0], view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
