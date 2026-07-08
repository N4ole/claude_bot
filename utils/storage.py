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
import os
from pathlib import Path
from threading import Lock


def _atomic_dump(path: Path, data) -> None:
    """Écrit du JSON de façon atomique : fichier temporaire puis os.replace.

    Évite qu'un crash en cours d'écriture ne laisse un fichier tronqué ou
    corrompu (os.replace est atomique sur un même système de fichiers).
    """
    tmp = path.with_name(f"{path.name}.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

# Dossier des données runtime (à la racine du projet).
_DATA = Path(__file__).resolve().parents[1] / "data"
_DATA.mkdir(exist_ok=True)

_STORE_PATH = _DATA / "watched.json"
_OWNERS_PATH = _DATA / "owners.json"
_WARNS_PATH = _DATA / "warns.json"
_CONFINE_PATH = _DATA / "confinements.json"
_SETTINGS_PATH = _DATA / "guild_settings.json"
_MODLOG_PATH = _DATA / "modlog.json"
_REMINDERS_PATH = _DATA / "reminders.json"
_TEMPBAN_PATH = _DATA / "tempbans.json"
_NOTES_PATH = _DATA / "notes.json"
_GIVEAWAYS_PATH = _DATA / "giveaways.json"
_BLACKLIST_PATH = _DATA / "guild_blacklist.json"
_lock = Lock()
_owners_lock = Lock()
_warns_lock = Lock()
_confine_lock = Lock()
_reminders_lock = Lock()
_settings_lock = Lock()
_modlog_lock = Lock()
_tempban_lock = Lock()
_notes_lock = Lock()
_giveaways_lock = Lock()
_blacklist_lock = Lock()


def _read() -> dict:
    if not _STORE_PATH.exists():
        return {}
    try:
        with _STORE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write(data: dict) -> None:
    _atomic_dump(_STORE_PATH, data)


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
    _atomic_dump(_OWNERS_PATH, owners)


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
    _atomic_dump(_WARNS_PATH, data)


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


def warn_totals() -> tuple[int, int]:
    """Renvoie (nombre d'utilisateurs avertis, total des points de warn)."""
    users, points = 0, 0
    for guild in _read_warns().values():
        for count in guild.values():
            users += 1
            points += int(count)
    return users, points


def total_watched() -> int:
    """Nombre total d'utilisateurs surveillés (tous serveurs confondus)."""
    return sum(len(users) for users in _read().values())


def count_setting_enabled(key: str) -> int:
    """Nombre de serveurs où le réglage `key` est activé."""
    return sum(1 for g in _read_settings().values() if g.get(key))


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
    _atomic_dump(_CONFINE_PATH, data)


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
# Bans temporaires (tempbans.json = {guild_id: {user_id: release_ts}})
# --------------------------------------------------------------------------- #
def _read_tempbans() -> dict:
    if not _TEMPBAN_PATH.exists():
        return {}
    try:
        with _TEMPBAN_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_tempbans(data: dict) -> None:
    _atomic_dump(_TEMPBAN_PATH, data)


def set_tempban(guild_id: int, user_id: int, release_ts: float) -> None:
    """Enregistre l'échéance (timestamp UTC) de déban d'un ban temporaire."""
    with _tempban_lock:
        data = _read_tempbans()
        data.setdefault(str(guild_id), {})[str(user_id)] = release_ts
        _write_tempbans(data)


def clear_tempban(guild_id: int, user_id: int) -> None:
    """Retire l'entrée de ban temporaire d'un utilisateur."""
    with _tempban_lock:
        data = _read_tempbans()
        guild = data.get(str(guild_id))
        if guild and str(user_id) in guild:
            del guild[str(user_id)]
            if not guild:
                del data[str(guild_id)]
            _write_tempbans(data)


def get_tempbans() -> list[tuple[int, int, float]]:
    """Renvoie tous les bans temporaires : (guild_id, user_id, ts)."""
    result = []
    for gid, users in _read_tempbans().items():
        for uid, ts in users.items():
            result.append((int(gid), int(uid), float(ts)))
    return result


# --------------------------------------------------------------------------- #
# Réglages par serveur (guild_settings.json = {guild_id: {clé: valeur}})
# --------------------------------------------------------------------------- #
# Cache mémoire des réglages : lus à chaque commande (routage des logs).
# Le fichier n'est écrit que via ce module (même processus), donc le cache
# est invalidé à chaque écriture — pas de risque de divergence.
_settings_cache: dict | None = None


def _read_settings() -> dict:
    global _settings_cache
    if _settings_cache is None:
        if not _SETTINGS_PATH.exists():
            _settings_cache = {}
        else:
            try:
                with _SETTINGS_PATH.open("r", encoding="utf-8") as f:
                    _settings_cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                _settings_cache = {}
    return _settings_cache


def _write_settings(data: dict) -> None:
    global _settings_cache
    _atomic_dump(_SETTINGS_PATH, data)
    _settings_cache = data


def get_setting(guild_id: int, key: str, default=None):
    """Renvoie la valeur d'un réglage de serveur, ou `default`."""
    return _read_settings().get(str(guild_id), {}).get(key, default)


def set_setting(guild_id: int, key: str, value) -> None:
    """Définit la valeur d'un réglage de serveur."""
    with _settings_lock:
        data = _read_settings()
        data.setdefault(str(guild_id), {})[key] = value
        _write_settings(data)


def get_prefix(guild_id: int | None) -> str:
    """Préfixe des commandes pour un serveur (réglage `prefix`, persisté).

    Repli sur le préfixe par défaut (`config.PREFIX`, via .env) si le
    serveur n'a rien personnalisé — et en MP (guild_id None).
    """
    import config  # import local : évite un cycle au chargement.

    if guild_id is None:
        return config.PREFIX
    return get_setting(guild_id, "prefix", config.PREFIX) or config.PREFIX


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
    _atomic_dump(_MODLOG_PATH, data)


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


def get_guild_modlog(guild_id: int) -> list[dict]:
    """Renvoie toutes les actions de modération d'un serveur.

    Chaque entrée est complétée par la clé `user_id` (cible de l'action).
    Trié par horodatage croissant.
    """
    result = []
    for uid, entries in _read_modlog().get(str(guild_id), {}).items():
        for entry in entries:
            result.append({**entry, "user_id": int(uid)})
    result.sort(key=lambda e: e.get("ts", 0))
    return result


# --------------------------------------------------------------------------- #
# Notes de dossier (notes.json = {guild_id: {user_id: [notes]}})
#   note = {"ts", "moderator", "text"}
# --------------------------------------------------------------------------- #
def _read_notes() -> dict:
    if not _NOTES_PATH.exists():
        return {}
    try:
        with _NOTES_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_notes(data: dict) -> None:
    _atomic_dump(_NOTES_PATH, data)


def add_note(
    guild_id: int, user_id: int, moderator_id: int, text: str
) -> None:
    """Ajoute une note libre au dossier d'un utilisateur (affichée par
    `userstatus`)."""
    from datetime import datetime, timezone

    entry = {
        "ts": datetime.now(timezone.utc).timestamp(),
        "moderator": moderator_id,
        "text": text,
    }
    with _notes_lock:
        data = _read_notes()
        data.setdefault(str(guild_id), {}).setdefault(
            str(user_id), []
        ).append(entry)
        _write_notes(data)


def get_notes(guild_id: int, user_id: int) -> list[dict]:
    """Renvoie les notes de dossier d'un utilisateur (ordre d'ajout)."""
    return _read_notes().get(str(guild_id), {}).get(str(user_id), [])


def remove_note(guild_id: int, user_id: int, index: int) -> dict | None:
    """Supprime la note d'indice `index` (0-based) et la renvoie, ou None."""
    with _notes_lock:
        data = _read_notes()
        notes = data.get(str(guild_id), {}).get(str(user_id), [])
        if not (0 <= index < len(notes)):
            return None
        removed = notes.pop(index)
        if not notes:
            data[str(guild_id)].pop(str(user_id), None)
            if not data[str(guild_id)]:
                data.pop(str(guild_id), None)
        _write_notes(data)
        return removed


# --------------------------------------------------------------------------- #
# Rappels (reminders.json = liste de rappels)
#   {"id", "user_id", "channel_id", "message", "due"}
# --------------------------------------------------------------------------- #
def _read_reminders() -> list[dict]:
    if not _REMINDERS_PATH.exists():
        return []
    try:
        with _REMINDERS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write_reminders(data: list[dict]) -> None:
    _atomic_dump(_REMINDERS_PATH, data)


def add_reminder(
    user_id: int, channel_id: int, message: str, due_ts: float
) -> dict:
    """Enregistre un rappel et le renvoie (avec son id)."""
    with _reminders_lock:
        data = _read_reminders()
        entry = {
            "id": (max((r["id"] for r in data), default=0) + 1),
            "user_id": user_id,
            "channel_id": channel_id,
            "message": message,
            "due": due_ts,
        }
        data.append(entry)
        _write_reminders(data)
        return entry


def remove_reminder(reminder_id: int) -> None:
    """Supprime un rappel par son id."""
    with _reminders_lock:
        data = [r for r in _read_reminders() if r["id"] != reminder_id]
        _write_reminders(data)


def get_reminders() -> list[dict]:
    """Renvoie tous les rappels en attente."""
    return _read_reminders()


# --------------------------------------------------------------------------- #
# Giveaways (giveaways.json = liste de giveaways)
#   {"message_id","channel_id","guild_id","prize","winners","end","host_id",
#    "ended"}
# --------------------------------------------------------------------------- #
def _read_giveaways() -> list[dict]:
    if not _GIVEAWAYS_PATH.exists():
        return []
    try:
        with _GIVEAWAYS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write_giveaways(data: list[dict]) -> None:
    _atomic_dump(_GIVEAWAYS_PATH, data)


def add_giveaway(
    message_id: int, channel_id: int, guild_id: int, prize: str,
    winners: int, end_ts: float, host_id: int,
) -> dict:
    """Enregistre un giveaway en cours et le renvoie."""
    with _giveaways_lock:
        data = _read_giveaways()
        entry = {
            "message_id": message_id,
            "channel_id": channel_id,
            "guild_id": guild_id,
            "prize": prize,
            "winners": winners,
            "end": end_ts,
            "host_id": host_id,
            "ended": False,
        }
        data.append(entry)
        _write_giveaways(data)
        return entry


def get_giveaway(message_id: int) -> dict | None:
    """Renvoie un giveaway par l'id de son message, ou None."""
    for g in _read_giveaways():
        if g["message_id"] == message_id:
            return g
    return None


def get_active_giveaways() -> list[dict]:
    """Renvoie les giveaways non encore terminés."""
    return [g for g in _read_giveaways() if not g.get("ended")]


def mark_giveaway_ended(message_id: int) -> None:
    """Marque un giveaway comme terminé (conservé pour un éventuel reroll)."""
    with _giveaways_lock:
        data = _read_giveaways()
        for g in data:
            if g["message_id"] == message_id:
                g["ended"] = True
        _write_giveaways(data)


def remove_giveaway(message_id: int) -> None:
    """Supprime définitivement un giveaway du stockage."""
    with _giveaways_lock:
        data = [g for g in _read_giveaways() if g["message_id"] != message_id]
        _write_giveaways(data)


# --------------------------------------------------------------------------- #
# Blacklist de serveurs (guild_blacklist.json = liste d'IDs de serveurs)
# --------------------------------------------------------------------------- #
def _read_blacklist() -> list[int]:
    if not _BLACKLIST_PATH.exists():
        return []
    try:
        with _BLACKLIST_PATH.open("r", encoding="utf-8") as f:
            return [int(x) for x in json.load(f)]
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return []


def _write_blacklist(data: list[int]) -> None:
    _atomic_dump(_BLACKLIST_PATH, data)


def add_blacklisted_guild(guild_id: int) -> bool:
    """Blackliste un serveur. Renvoie False s'il l'était déjà."""
    with _blacklist_lock:
        data = _read_blacklist()
        if guild_id in data:
            return False
        data.append(guild_id)
        _write_blacklist(data)
        return True


def remove_blacklisted_guild(guild_id: int) -> bool:
    """Retire un serveur de la blacklist. Renvoie False s'il n'y était pas."""
    with _blacklist_lock:
        data = _read_blacklist()
        if guild_id not in data:
            return False
        data.remove(guild_id)
        _write_blacklist(data)
        return True


def is_blacklisted_guild(guild_id: int) -> bool:
    """True si le serveur est blacklisté."""
    return guild_id in _read_blacklist()


def get_blacklisted_guilds() -> list[int]:
    """Renvoie la liste des serveurs blacklistés."""
    return _read_blacklist()
