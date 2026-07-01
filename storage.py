"""Persistance des utilisateurs surveillés dans un fichier JSON.

Structure du fichier :
    {
        "<guild_id>": {
            "<user_id>": <channel_id>,
            ...
        },
        ...
    }
"""
import json
from pathlib import Path
from threading import Lock

_STORE_PATH = Path(__file__).parent / "watched.json"
_OWNERS_PATH = Path(__file__).parent / "owners.json"
_lock = Lock()
_owners_lock = Lock()


def _read() -> dict:
    if not _STORE_PATH.exists():
        return {}
    try:
        with _STORE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write(data: dict) -> None:
    with _STORE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_watch(guild_id: int, user_id: int, channel_id: int) -> None:
    """Enregistre un utilisateur surveillé et le salon de log associé."""
    with _lock:
        data = _read()
        data.setdefault(str(guild_id), {})[str(user_id)] = channel_id
        _write(data)


def remove_watch(guild_id: int, user_id: int) -> None:
    """Retire un utilisateur de la surveillance."""
    with _lock:
        data = _read()
        guild = data.get(str(guild_id))
        if guild and str(user_id) in guild:
            del guild[str(user_id)]
            if not guild:
                del data[str(guild_id)]
            _write(data)


def get_channel_id(guild_id: int, user_id: int) -> int | None:
    """Renvoie l'ID du salon de log si l'utilisateur est surveillé, sinon None."""
    return _read().get(str(guild_id), {}).get(str(user_id))


def get_guild_watches(guild_id: int) -> dict[int, int]:
    """Renvoie {user_id: channel_id} pour tous les surveillés d'un serveur."""
    return {
        int(uid): cid
        for uid, cid in _read().get(str(guild_id), {}).items()
    }


# --------------------------------------------------------------------------- #
# Owners additionnels (owners.json = liste d'IDs)
# --------------------------------------------------------------------------- #
def _read_owners() -> list[int]:
    if not _OWNERS_PATH.exists():
        return []
    try:
        with _OWNERS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [int(x) for x in data]
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return []


def _write_owners(owners: list[int]) -> None:
    with _OWNERS_PATH.open("w", encoding="utf-8") as f:
        json.dump(owners, f, indent=2)


def get_owners() -> list[int]:
    """Renvoie la liste des owners additionnels (hors owner principal)."""
    return _read_owners()


def add_owner(user_id: int) -> bool:
    """Ajoute un owner. Renvoie False s'il était déjà présent."""
    with _owners_lock:
        owners = _read_owners()
        if user_id in owners:
            return False
        owners.append(user_id)
        _write_owners(owners)
        return True


def remove_owner(user_id: int) -> bool:
    """Retire un owner. Renvoie False s'il n'était pas présent."""
    with _owners_lock:
        owners = _read_owners()
        if user_id not in owners:
            return False
        owners.remove(user_id)
        _write_owners(owners)
        return True
