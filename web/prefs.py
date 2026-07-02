"""Préférences par compte pour le panel web (data/web_prefs.json).

Stocke, par identifiant Discord, la langue choisie sur le panel. Persisté sur
disque : le choix survit aux redémarrages et suit le compte (pas le navigateur).
"""
import json
from pathlib import Path
from threading import Lock

_DATA = Path(__file__).resolve().parents[1] / "data"
_DATA.mkdir(exist_ok=True)
_PATH = _DATA / "web_prefs.json"
_lock = Lock()

LANGS = ("fr", "en")
DEFAULT = "fr"


def _read() -> dict:
    if not _PATH.exists():
        return {}
    try:
        with _PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write(data: dict) -> None:
    with _PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_lang(user_id) -> str:
    """Langue enregistrée pour un compte, ou la langue par défaut."""
    lang = _read().get(str(user_id), {}).get("lang", DEFAULT)
    return lang if lang in LANGS else DEFAULT


def set_lang(user_id, lang: str) -> None:
    """Enregistre la langue d'un compte."""
    if lang not in LANGS:
        return
    with _lock:
        data = _read()
        data.setdefault(str(user_id), {})["lang"] = lang
        _write(data)
