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

BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE="${DEPLOY_SERVICE:-watcher}"
PYTHON="${DEPLOY_PYTHON:-python3}"

# Se placer à la racine du dépôt (le script est dans scripts/).
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

log() { printf '[deploy] %s\n' "$*"; }

# Verrou simple pour éviter deux déploiements simultanés (cron rapproché).
LOCK="${REPO_ROOT}/.deploy.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
    log "Un déploiement est déjà en cours (verrou $LOCK) — abandon."
    exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

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

# Redémarre le service s'il existe, sinon prévient l'opérateur.
if command -v systemctl >/dev/null 2>&1 \
    && systemctl list-unit-files "${SERVICE}.service" >/dev/null 2>&1; then
    log "Redémarrage du service ${SERVICE}."
    sudo systemctl restart "$SERVICE"
else
    log "Service systemd '${SERVICE}' introuvable."
    log "Redémarre le bot manuellement pour appliquer la mise à jour."
fi

log "Déploiement terminé (${REMOTE:0:8})."
