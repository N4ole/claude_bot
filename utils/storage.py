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

# Dossier des données runtime (à la racine du projet).
_DATA = Path(__file__).resolve().parents[1] / "data"
_DATA.mkdir(exist_ok=True)

_STORE_PATH = _DATA / "watched.json"
_OWNERS_PATH = _DATA / "owners.json"
_WARNS_PATH = _DATA / "warns.json"
_CONFINE_PATH = _DATA / "confinements.json"
_SETTINGS_PATH = _DATA / "guild_settings.json"
_MODLOG_PATH = _DATA / "modlog.json"
_lock = Lock()
_owners_lock = Lock()
_warns_lock = Lock()
_confine_lock = Lock()
_settings_lock = Lock()
_modlog_lock = Lock()


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


# --------------------------------------------------------------------------- #
# Avertissements (warns.json = {guild_id: {user_id: count}})
# --------------------------------------------------------------------------- #
def _read_warns() -> dict:
    if not _WARNS_PATH.exists():
        return {}
    try:
        with _WARNS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_warns(data: dict) -> None:
    with _WARNS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_warns(guild_id: int, user_id: int) -> int:
    """Renvoie le nombre d'avertissements d'un utilisateur."""
    return _read_warns().get(str(guild_id), {}).get(str(user_id), 0)


def add_warn(guild_id: int, user_id: int) -> int:
    """Incrémente les avertissements d'un utilisateur et renvoie le total."""
    with _warns_lock:
        data = _read_warns()
        guild = data.setdefault(str(guild_id), {})
        guild[str(user_id)] = guild.get(str(user_id), 0) + 1
        _write_warns(data)
        return guild[str(user_id)]


def set_warns(guild_id: int, user_id: int, count: int) -> None:
    """Fixe le nombre d'avertissements (supprime l'entrée si <= 0)."""
    with _warns_lock:
        data = _read_warns()
        guild = data.setdefault(str(guild_id), {})
        if count <= 0:
            guild.pop(str(user_id), None)
            if not guild:
                data.pop(str(guild_id), None)
        else:
            guild[str(user_id)] = count
        _write_warns(data)


# --------------------------------------------------------------------------- #
# Confinements temporisés
#   confinements.json = {guild_id: {user_id: release_timestamp_utc}}
# --------------------------------------------------------------------------- #
def _read_confinements() -> dict:
    if not _CONFINE_PATH.exists():
        return {}
    try:
        with _CONFINE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_confinements(data: dict) -> None:
    with _CONFINE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def set_confinement(guild_id: int, user_id: int, release_ts: float) -> None:
    """Enregistre l'échéance (timestamp UTC) de libération d'un confinement."""
    with _confine_lock:
        data = _read_confinements()
        data.setdefault(str(guild_id), {})[str(user_id)] = release_ts
        _write_confinements(data)


def clear_confinement(guild_id: int, user_id: int) -> None:
    """Retire l'entrée de confinement temporisé d'un utilisateur."""
    with _confine_lock:
        data = _read_confinements()
        guild = data.get(str(guild_id))
        if guild and str(user_id) in guild:
            del guild[str(user_id)]
            if not guild:
                del data[str(guild_id)]
            _write_confinements(data)


def get_confinements() -> list[tuple[int, int, float]]:
    """Renvoie tous les confinements temporisés : (guild_id, user_id, ts)."""
    result = []
    for gid, users in _read_confinements().items():
        for uid, ts in users.items():
            result.append((int(gid), int(uid), float(ts)))
    return result


# --------------------------------------------------------------------------- #
# Réglages par serveur (guild_settings.json = {guild_id: {clé: valeur}})
# --------------------------------------------------------------------------- #
def _read_settings() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        with _SETTINGS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_settings(data: dict) -> None:
    with _SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_setting(guild_id: int, key: str, default=None):
    """Renvoie la valeur d'un réglage de serveur, ou `default`."""
    return _read_settings().get(str(guild_id), {}).get(key, default)


def set_setting(guild_id: int, key: str, value) -> None:
    """Définit la valeur d'un réglage de serveur."""
    with _settings_lock:
        data = _read_settings()
        data.setdefault(str(guild_id), {})[key] = value
        _write_settings(data)


# --------------------------------------------------------------------------- #
# Journal de modération (modlog.json = {guild_id: {user_id: [actions]}})
#   action = {"type", "ts", "duration"(s|None), "detail", "moderator"}
# --------------------------------------------------------------------------- #
def _read_modlog() -> dict:
    if not _MODLOG_PATH.exists():
        return {}
    try:
        with _MODLOG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_modlog(data: dict) -> None:
    with _MODLOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_modlog(
    guild_id: int,
    user_id: int,
    action_type: str,
    moderator_id: int | None = None,
    duration: float | None = None,
    detail: str | None = None,
) -> None:
    """Ajoute une action de modération à l'historique d'un utilisateur."""
    from datetime import datetime, timezone

    entry = {
        "type": action_type,
        "ts": datetime.now(timezone.utc).timestamp(),
        "duration": duration,
        "detail": detail,
        "moderator": moderator_id,
    }
    with _modlog_lock:
        data = _read_modlog()
        data.setdefault(str(guild_id), {}).setdefault(
            str(user_id), []
        ).append(entry)
        _write_modlog(data)


def get_modlog(guild_id: int, user_id: int) -> list[dict]:
    """Renvoie l'historique de modération d'un utilisateur."""
    return _read_modlog().get(str(guild_id), {}).get(str(user_id), [])
