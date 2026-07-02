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
