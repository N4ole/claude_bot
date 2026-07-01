"""Collecte de statistiques quotidiennes par serveur (pour la commande analyse).

analytics.json :
    { "<guild_id>": { "YYYY-MM-DD": {
        "messages": int, "joins": int, "leaves": int, "members": int } } }
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

_DATA = Path(__file__).resolve().parents[1] / "data"
_DATA.mkdir(exist_ok=True)
_PATH = _DATA / "analytics.json"
_lock = Lock()

# On ne conserve que les 60 derniers jours.
_KEEP_DAYS = 60


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


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
        json.dump(data, f)


def _day_entry(day: dict) -> dict:
    for key in ("messages", "joins", "leaves", "members"):
        day.setdefault(key, 0)
    return day


def add_counts(
    guild_id: int, *, messages: int = 0, joins: int = 0, leaves: int = 0
) -> None:
    """Incrémente les compteurs du jour courant pour un serveur."""
    if not (messages or joins or leaves):
        return
    with _lock:
        data = _read()
        guild = data.setdefault(str(guild_id), {})
        day = _day_entry(guild.setdefault(_today(), {}))
        day["messages"] += messages
        day["joins"] += joins
        day["leaves"] += leaves
        _write(data)


def set_members(guild_id: int, count: int) -> None:
    """Fixe le nombre de membres du jour courant + purge l'historique ancien."""
    with _lock:
        data = _read()
        guild = data.setdefault(str(guild_id), {})
        day = _day_entry(guild.setdefault(_today(), {}))
        day["members"] = count
        # Purge des jours trop anciens.
        limit = (
            datetime.now(timezone.utc) - timedelta(days=_KEEP_DAYS)
        ).strftime("%Y-%m-%d")
        for d in [d for d in guild if d < limit]:
            del guild[d]
        _write(data)


def get_range(guild_id: int, days: int) -> list[dict]:
    """Renvoie les `days` derniers jours (du plus ancien au plus récent).

    Chaque élément : {date, messages, joins, leaves, members}.
    """
    guild = _read().get(str(guild_id), {})
    today = datetime.now(timezone.utc).date()
    result = []
    for i in range(days - 1, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        entry = guild.get(date, {})
        result.append(
            {
                "date": date,
                "messages": entry.get("messages", 0),
                "joins": entry.get("joins", 0),
                "leaves": entry.get("leaves", 0),
                "members": entry.get("members", 0),
            }
        )
    return result
