"""Persistance des statistiques du bot pour le panel web.

Fichier stats.json :
    {
        "snapshots": [ {"ts": <epoch>, "guilds": <int>, "members": <int>} ],
        "guilds": {
            "<guild_id>": {
                "name": "<str>",
                "members": [ {"ts": <epoch>, "count": <int>} ]
            }
        },
        "usage": { "<guild_id>": { "YYYY-MM-DD": <int> } }
    }
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_PATH = Path(__file__).parent / "stats.json"
_lock = Lock()

# Nombre maximal de points conservés par série temporelle.
_MAX_POINTS = 1000


def _read() -> dict:
    if not _PATH.exists():
        return {"snapshots": [], "guilds": {}, "usage": {}}
    try:
        with _PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"snapshots": [], "guilds": {}, "usage": {}}
    data.setdefault("snapshots", [])
    data.setdefault("guilds", {})
    data.setdefault("usage", {})
    return data


def _write(data: dict) -> None:
    with _PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f)


def record_snapshot(guilds: list[tuple[int, str, int]]) -> None:
    """Enregistre un instantané global + par serveur.

    `guilds` : liste de (guild_id, nom, nombre_de_membres).
    """
    now = datetime.now(timezone.utc).timestamp()
    total_members = sum(count for _, _, count in guilds)
    with _lock:
        data = _read()
        data["snapshots"].append(
            {"ts": now, "guilds": len(guilds), "members": total_members}
        )
        data["snapshots"] = data["snapshots"][-_MAX_POINTS:]

        for guild_id, name, count in guilds:
            entry = data["guilds"].setdefault(
                str(guild_id), {"name": name, "members": []}
            )
            entry["name"] = name
            entry["members"].append({"ts": now, "count": count})
            entry["members"] = entry["members"][-_MAX_POINTS:]
        _write(data)


def record_usage(guild_id: int) -> None:
    """Incrémente le compteur d'utilisation d'un serveur pour aujourd'hui."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        data = _read()
        guild_usage = data["usage"].setdefault(str(guild_id), {})
        guild_usage[today] = guild_usage.get(today, 0) + 1
        _write(data)


def get_snapshots() -> list[dict]:
    return _read()["snapshots"]


def get_guild_stats(guild_id: int) -> dict | None:
    data = _read()
    entry = data["guilds"].get(str(guild_id))
    if entry is None:
        return None
    usage = data["usage"].get(str(guild_id), {})
    return {
        "name": entry.get("name", str(guild_id)),
        "members": entry.get("members", []),
        "usage": [{"date": d, "count": c} for d, c in sorted(usage.items())],
    }
