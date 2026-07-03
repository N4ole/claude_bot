"""Génère la documentation par commande et par catégorie.

Introspecte les commandes chargées par le bot et écrit :
  - docs/commands/<commande>.md   (une fiche par commande)
  - docs/categories/<slug>.md     (une page par catégorie)
  - docs/commands/README.md       (index des commandes)

Usage :  python -m scripts.gen_docs
"""
import asyncio
import re
import unicodedata
from pathlib import Path

import config
from bot import Watcher
from utils import categories as cats
from utils.i18n import t

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CMD_DIR = DOCS / "commands"
CAT_DIR = DOCS / "categories"

OWNER_CATEGORY = ("👑 Owner du bot", None)


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _category_of(command) -> tuple[str, str | None]:
    """(nom de catégorie affiché, libellé de permission) — via utils.categories."""
    if command.module and command.module.startswith("cogs.owner"):
        return OWNER_CATEGORY
    cat_key, perm_key = cats.category_of(command)
    return t(None, cat_key), (t(None, perm_key) if perm_key else None)


def _availability(command) -> str:
    from discord.ext import commands as dcommands
    return (
        "préfixe (`" + config.PREFIX + "`) et slash (`/`)"
        if isinstance(command, dcommands.HybridCommand)
        else "préfixe uniquement"
    )


def _command_doc(command) -> str:
    category, perm = _category_of(command)
    signature = command.signature.strip()
    usage = f"{config.PREFIX}{command.qualified_name}"
    if signature:
        usage += f" {signature}"
    lines = [
        f"# `{config.PREFIX}{command.qualified_name}`",
        "",
        command.description or command.help or "_Pas de description._",
        "",
        f"- **Catégorie** : {category}",
        f"- **Permission** : {perm or 'Aucune'}",
        f"- **Disponible en** : {_availability(command)}",
        f"- **Usage** : `{usage}`",
    ]
    if command.aliases:
        lines.append(
            "- **Alias** : " + ", ".join(f"`{a}`" for a in command.aliases)
        )
    lines += [
        "",
        "> Légende : `<...>` argument obligatoire · `[...]` facultatif.",
        "",
    ]
    return "\n".join(lines)


def _category_doc(name: str, commands_list: list) -> str:
    lines = [f"# {name}", ""]
    for command in sorted(commands_list, key=lambda c: c.qualified_name):
        _, perm = _category_of(command)
        desc = command.description or "Pas de description."
        perm_txt = f" — 🔒 *{perm}*" if perm else ""
        slug = _slug(command.qualified_name)
        lines.append(
            f"- [`{config.PREFIX}{command.qualified_name}`](../commands/{slug}.md)"
            f" — {desc}{perm_txt}"
        )
    lines.append("")
    return "\n".join(lines)


async def main() -> None:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CAT_DIR.mkdir(parents=True, exist_ok=True)

    bot = Watcher()
    await bot._load_cogs()
    commands_all = sorted(bot.commands, key=lambda c: c.qualified_name)

    categories: dict[str, list] = {}
    index_lines = ["# Index des commandes", ""]
    for command in commands_all:
        (CMD_DIR / f"{_slug(command.qualified_name)}.md").write_text(
            _command_doc(command), encoding="utf-8"
        )
        category, _ = _category_of(command)
        categories.setdefault(category, []).append(command)
        index_lines.append(
            f"- [`{config.PREFIX}{command.qualified_name}`]"
            f"({_slug(command.qualified_name)}.md)"
        )
    (CMD_DIR / "README.md").write_text("\n".join(index_lines) + "\n", "utf-8")

    cat_index = ["# Catégories", ""]
    for name, cmds in sorted(categories.items()):
        (CAT_DIR / f"{_slug(name)}.md").write_text(
            _category_doc(name, cmds), encoding="utf-8"
        )
        cat_index.append(f"- [{name}]({_slug(name)}.md) ({len(cmds)} commandes)")
    (CAT_DIR / "README.md").write_text("\n".join(cat_index) + "\n", "utf-8")

    await bot.close()
    print(
        f"Docs générées : {len(commands_all)} commandes, "
        f"{len(categories)} catégories."
    )


if __name__ == "__main__":
    asyncio.run(main())
