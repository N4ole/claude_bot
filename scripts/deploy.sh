#!/usr/bin/env bash
#
# Déploiement automatique de Watcher depuis GitHub.
#
# Récupère la dernière version de la branche suivie, remplace le code local
# par celui de GitHub, réinstalle les dépendances si besoin, puis redémarre
# le service. Idempotent : ne fait rien (et ne redémarre pas) si le dépôt
# est déjà à jour.
#
# Usage :
#   scripts/deploy.sh
#
# Variables d'environnement :
#   DEPLOY_BRANCH   branche à déployer (défaut : main)
#   DEPLOY_SERVICE  nom du service systemd à redémarrer (défaut : watcher)
#   DEPLOY_PYTHON   interpréteur pour pip (défaut : python3)
#
# Pour un déploiement « à chaque push », lancer ce script périodiquement via
# cron (voir docs/DEPLOY.md). Les fichiers non suivis (data/*.json, logs/,
# .env) ne sont PAS touchés par la mise à jour.

set -euo pipefail

# --- Auto-protection --------------------------------------------------------
# Le `git reset --hard` plus bas remplace CE script pendant qu'il s'exécute
# (cas où une mise à jour modifie deploy.sh lui-même). Pour ne jamais scier la
# branche sur laquelle on est assis, on se ré-exécute depuis une copie
# temporaire hors du dépôt ; la version d'origine du script va alors au bout,
# et la nouvelle version s'appliquera au prochain déploiement.
if [ -z "${DEPLOY_SELF_COPY:-}" ]; then
    DEPLOY_REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    export DEPLOY_REPO_ROOT
    _self_copy="$(mktemp "${TMPDIR:-/tmp}/watcher-deploy.XXXXXX")"
    cp "$0" "$_self_copy"
    DEPLOY_SELF_COPY="$_self_copy" exec bash "$_self_copy" "$@"
fi

BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE="${DEPLOY_SERVICE:-watcher}"
PYTHON="${DEPLOY_PYTHON:-python3}"

# Racine du dépôt, transmise par la phase d'auto-copie ci-dessus.
cd "$DEPLOY_REPO_ROOT"
REPO_ROOT="$(pwd)"

log() { printf '[deploy] %s\n' "$*"; }

# Verrou simple pour éviter deux déploiements simultanés (cron rapproché).
LOCK="${REPO_ROOT}/.deploy.lock"
cleanup() {
    rmdir "$LOCK" 2>/dev/null || true
    rm -f "$DEPLOY_SELF_COPY" 2>/dev/null || true
}
if ! mkdir "$LOCK" 2>/dev/null; then
    log "Un déploiement est déjà en cours (verrou $LOCK) — abandon."
    rm -f "$DEPLOY_SELF_COPY" 2>/dev/null || true
    exit 0
fi
trap cleanup EXIT

git fetch --quiet origin "$BRANCH"

LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "origin/${BRANCH}")"

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Déjà à jour (${LOCAL:0:8}) sur ${BRANCH}."
    exit 0
fi

log "Mise à jour ${LOCAL:0:8} -> ${REMOTE:0:8} (${BRANCH})."

# Remplace le code local par celui de GitHub (les fichiers gitignorés,
# dont data/ et .env, sont conservés).
git reset --hard "origin/${BRANCH}"

# Réinstalle les dépendances uniquement si requirements.txt a changé.
if git diff --name-only "$LOCAL" "$REMOTE" | grep -q '^requirements.txt$'; then
    log "requirements.txt modifié — installation des dépendances."
    "$PYTHON" -m pip install -r requirements.txt --quiet
fi

# Note de déploiement : au redémarrage, le bot préviendra les owners en MP
# (PR concernées, commits, version). Fichier gitignoré, préservé par le reset.
mkdir -p "${REPO_ROOT}/data"
"$PYTHON" - "$LOCAL" "$REMOTE" "$BRANCH" <<'PY' || log "Note de déploiement non écrite (non bloquant)."
import datetime, json, pathlib, subprocess, sys
old, new, branch = sys.argv[1:4]
subjects = subprocess.run(
    ["git", "log", "--pretty=format:%h\t%s", f"{old}..{new}"],
    capture_output=True, text=True, check=False,
).stdout.splitlines()
pathlib.Path("data/pending_deploy.json").write_text(
    json.dumps(
        {
            "old": old[:8], "new": new[:8], "branch": branch,
            "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "commits": subjects,
        },
        ensure_ascii=False, indent=2,
    ),
    encoding="utf-8",
)
PY

# Redémarre le bot : service systemd si configuré, sinon process Python
# autonome via watcher-ctl.sh (voir docs/DEPLOY.md), sinon message manuel.
if command -v systemctl >/dev/null 2>&1 \
    && systemctl list-unit-files "${SERVICE}.service" >/dev/null 2>&1; then
    log "Redémarrage du service ${SERVICE}."
    sudo systemctl restart "$SERVICE"
elif [ -x "${REPO_ROOT}/scripts/watcher-ctl.sh" ]; then
    log "Redémarrage via watcher-ctl.sh (process Python autonome)."
    "${REPO_ROOT}/scripts/watcher-ctl.sh" restart
else
    log "Aucun mécanisme de redémarrage détecté (ni systemd ni watcher-ctl.sh)."
    log "Redémarre le bot manuellement pour appliquer la mise à jour."
fi

log "Déploiement terminé (${REMOTE:0:8})."
