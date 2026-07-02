"""Commande help : une page par catégorie, navigation par boutons."""
import discord
from discord.ext import commands

import config
from utils.i18n import t

# Catégorie (clé i18n) et permission (clé i18n ou None), par nom de cog.
_CATEGORIES = {
    # Infos
    "UserInfo": ("cat.info", None),
    "Avatar": ("cat.info", None),
    "ServerInfo": ("cat.info", None),
    "BotInfo": ("cat.info", None),
    "MemberCount": ("cat.info", None),
    # Utilitaire
    "Poll": ("cat.util", None),
    "Roll": ("cat.util", None),
    "CoinFlip": ("cat.util", None),
    "EightBall": ("cat.util", None),
    "Choose": ("cat.util", None),
    "RemindMe": ("cat.util", None),
    # Modération
    "Watch": ("cat.mod", "perm.admin"),
    "Confine": ("cat.mod", "perm.admin"),
    "Mute": ("cat.mod", "perm.admin"),
    "Warn": ("cat.mod", "perm.admin"),
    "Clear": ("cat.mod", "perm.manage_messages"),
    "AntiBot": ("cat.mod", "perm.admin"),
    "AntiRaid": ("cat.mod", "perm.admin"),
    "AntiPub": ("cat.mod", "perm.admin"),
    "AntiSpam": ("cat.mod", "perm.admin"),
    "AntiInsulte": ("cat.mod", "perm.admin"),
    "Protections": ("cat.mod", "perm.admin"),
    "UserStatus": ("cat.mod", "perm.admin"),
    "Analyse": ("cat.mod", "perm.admin"),
    "Langue": ("cat.mod", "perm.admin"),
    # Propriétaire de serveur
    "ContactOwner": ("cat.owner_server", "perm.server_owner"),
}
_DEFAULT = ("cat.general", None)
_ORDER = [
    "cat.general", "cat.info", "cat.util", "cat.mod", "cat.owner_server",
]

# Discord limite la valeur d'un champ d'embed à 1024 caractères.
_FIELD_LIMIT = 1024


def _chunk_lines(lines: list[str]) -> list[list[str]]:
    """Regroupe des lignes en blocs dont le texte joint tient dans un champ."""
    chunks: list[list[str]] = []
    current: list[str] = []
    length = 0
    for line in lines:
        # +1 pour le saut de ligne entre deux entrées.
        extra = len(line) + (1 if current else 0)
        if current and length + extra > _FIELD_LIMIT:
            chunks.append(current)
            current = []
            length = 0
            extra = len(line)
        current.append(line)
        length += extra
    if current:
        chunks.append(current)
    return chunks


class HelpView(discord.ui.View):
    """Vue de navigation entre les pages d'aide."""

    def __init__(
        self, pages: list[discord.Embed], author_id: int, source
    ) -> None:
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0
        self.author_id = author_id
        self.source = source
        self._refresh()

    def _refresh(self) -> None:
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.pages) - 1
        self.counter.label = f"{self.index + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                t(self.source, "help.not_for_you"), ephemeral=True
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

    def _describe(self, ctx, command: commands.Command) -> str:
        """Description traduite de la commande, avec repli sur le décorateur."""
        key = f"cmddesc.{command.qualified_name}"
        translated = t(ctx, key)
        if translated != key:
            return translated
        return command.description or command.help or t(ctx, "help.no_desc")

    def _is_hidden(self, command: commands.Command) -> bool:
        """True si la commande ne doit pas apparaître dans l'aide publique."""
        if command.hidden:
            return True
        return bool(command.module and command.module.startswith("cogs.owner"))

    def _command_detail(self, ctx, command: commands.Command) -> discord.Embed:
        cat_key, perm_key = self._category_of(command)
        embed = discord.Embed(
            title=t(ctx, "help.cmd_title", prefix=config.PREFIX,
                    name=command.qualified_name),
            description=self._describe(ctx, command),
            color=discord.Color.blurple(),
        )
        signature = command.signature.strip()
        usage = f"{config.PREFIX}{command.qualified_name}"
        if signature:
            usage += f" {signature}"
        embed.add_field(name=t(ctx, "help.usage"), value=f"`{usage}`",
                        inline=False)
        embed.add_field(name=t(ctx, "help.category"), value=t(ctx, cat_key),
                        inline=True)
        embed.add_field(
            name=t(ctx, "help.permission"),
            value=f"🔒 {t(ctx, perm_key)}" if perm_key
            else t(ctx, "help.perm_none"),
            inline=True,
        )
        embed.add_field(
            name=t(ctx, "help.avail"),
            value=t(ctx, "help.avail_both", prefix=config.PREFIX)
            if isinstance(command, commands.HybridCommand)
            else t(ctx, "help.avail_prefix"),
            inline=True,
        )
        if command.aliases:
            embed.add_field(
                name=t(ctx, "help.alias"),
                value=", ".join(f"`{a}`" for a in command.aliases),
                inline=False,
            )
        embed.set_footer(text=t(ctx, "help.legend", prefix=config.PREFIX))
        return embed

    def _build_pages(self, ctx) -> list[discord.Embed]:
        grouped: dict[str, list[str]] = {}
        total = 0
        for command in sorted(self.bot.commands, key=lambda c: c.name):
            if self._is_hidden(command):
                continue
            cat_key, perm_key = self._category_of(command)
            desc = self._describe(ctx, command)
            line = f"`{config.PREFIX}{command.name}` — {desc}"
            if perm_key:
                line += f" 🔒 *{t(ctx, perm_key)}*"
            grouped.setdefault(cat_key, []).append(line)
            total += 1

        ordered = _ORDER + [c for c in grouped if c not in _ORDER]
        page_keys = [c for c in ordered if c in grouped]
        pages = []
        for i, cat_key in enumerate(page_keys):
            category = t(ctx, cat_key)
            embed = discord.Embed(
                title=t(ctx, "help.title", category=category),
                description=t(ctx, "help.desc", prefix=config.PREFIX),
                color=discord.Color.blurple(),
            )
            # Discord limite la valeur d'un champ à 1024 caractères : on
            # découpe les catégories chargées (ex. Modération) en plusieurs
            # champs pour que la page reste affichable.
            for chunk in _chunk_lines(grouped[cat_key]):
                embed.add_field(
                    name=category, value="\n".join(chunk), inline=False
                )
                category = "​"  # champs suivants : nom invisible.
            embed.set_footer(
                text=t(ctx, "help.page", n=i + 1, total=len(page_keys),
                       count=total)
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
                await ctx.send(t(ctx, "help.not_found", cmd=commande))
                return
            await ctx.send(embed=self._command_detail(ctx, command))
            return

        # Aide générale paginée.
        pages = self._build_pages(ctx)
        if not pages:
            await ctx.send(t(ctx, "help.no_cmd"))
            return
        view = HelpView(pages, ctx.author.id, ctx.guild)
        await ctx.send(embed=pages[0], view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
