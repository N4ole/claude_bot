"""Journalisation des événements côté serveur dans des fichiers triés.

Installe des handlers de fichiers, en plus de la console, pour conserver
une trace durable et organisée de l'activité du bot. Les logs sont :

* **triés par catégorie** dans des fichiers distincts :
    - ``logs/bot.log``     : tout l'historique (INFO et plus) ;
    - ``logs/actions.log`` : uniquement les actions du bot (commandes,
      arrivées/départs de serveurs, sanctions d'automodération…) ;
    - ``logs/errors.log``  : uniquement les avertissements et erreurs ;
* **datés et complets** : chaque ligne contient la date et l'heure
  précises, le niveau, le logger d'origine, le module, la fonction et la
  ligne de code, puis le message ;
* **découpés par jour** : rotation quotidienne à minuit, avec conservation
  d'un historique glissant (30 jours par défaut).
"""
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Répertoire des journaux, à la racine du projet.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# Format détaillé : tout ce qu'il faut pour retrouver l'origine d'un log.
_DETAILED = logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s "
    "(%(module)s.%(funcName)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Nombre de jours d'historique conservés par fichier.
_BACKUP_DAYS = 30

# --- Couleurs console (codes ANSI) ---
_RESET = "\033[0m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
# Couleur associée à chaque niveau de log.
_LEVEL_COLORS = {
    logging.DEBUG: "\033[36m",     # cyan
    logging.INFO: "\033[32m",      # vert
    logging.WARNING: "\033[33m",   # jaune
    logging.ERROR: "\033[31m",     # rouge
    logging.CRITICAL: "\033[1;97;41m",  # blanc gras sur fond rouge
}


class ColorFormatter(logging.Formatter):
    """Formateur console : colore l'heure, le niveau et le nom du logger.

    Les couleurs (codes ANSI) ne sont appliquées que si la sortie est un
    vrai terminal, pour ne pas polluer les redirections vers un fichier.
    """

    def __init__(self, *, color: bool = True) -> None:
        super().__init__(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        if not self.color:
            return super().format(record)
        # On ne mute jamais le record (partagé avec les handlers fichiers et
        # le tampon web) : on assemble la ligne colorée à la main.
        level_color = _LEVEL_COLORS.get(record.levelno, "")
        ts = self.formatTime(record, self.datefmt)
        msg = record.getMessage()
        if record.exc_info:
            msg = f"{msg}\n{self.formatException(record.exc_info)}"
        if record.stack_info:
            msg = f"{msg}\n{self.formatStack(record.stack_info)}"
        return (
            f"{_DIM}{ts}{_RESET} "
            f"[{level_color}{_BOLD}{record.levelname}{_RESET}] "
            f"{_DIM}{record.name}{_RESET}: "
            f"{level_color}{msg}{_RESET}"
        )


def console_handler() -> logging.StreamHandler:
    """Crée le handler console coloré (couleur auto selon TTY)."""
    handler = logging.StreamHandler()
    use_color = hasattr(handler.stream, "isatty") and handler.stream.isatty()
    handler.setFormatter(ColorFormatter(color=use_color))
    return handler


class _ActionFilter(logging.Filter):
    """Ne laisse passer que les événements du logger « action »."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == "action" or record.name.startswith("action.")


def _daily_handler(
    path: Path, level: int, *, filt: logging.Filter | None = None
) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        path, when="midnight", backupCount=_BACKUP_DAYS, encoding="utf-8"
    )
    # Suffixe des fichiers pivotés : bot.log.2026-07-02
    handler.suffix = "%Y-%m-%d"
    handler.setLevel(level)
    handler.setFormatter(_DETAILED)
    if filt is not None:
        handler.addFilter(filt)
    return handler


def install() -> None:
    """Installe les handlers de fichiers sur le logger racine (idempotent)."""
    root = logging.getLogger()
    # Marqueur d'idempotence pour éviter les doublons au rechargement.
    if getattr(install, "_done", False):
        return

    LOG_DIR.mkdir(exist_ok=True)

    # Historique complet (tout ce qui atteint la console).
    root.addHandler(_daily_handler(LOG_DIR / "bot.log", logging.INFO))
    # Actions du bot uniquement (qui / quoi / où / quand).
    root.addHandler(
        _daily_handler(
            LOG_DIR / "actions.log", logging.INFO, filt=_ActionFilter()
        )
    )
    # Avertissements et erreurs uniquement.
    root.addHandler(_daily_handler(LOG_DIR / "errors.log", logging.WARNING))

    install._done = True  # type: ignore[attr-defined]
