#!/usr/bin/env bash
#
# Installe le LANCEMENT PÉRIODIQUE du déploiement (scripts/deploy.sh), pour
# que tout push sur GitHub se déploie automatiquement sur le serveur.
#
# Usage :
#   scripts/install-autodeploy.sh [systemd|cron]
#
# Défaut : systemd (timer). Variables :
#   DEPLOY_INTERVAL_MIN   intervalle en minutes (défaut : 1)
#   DEPLOY_BRANCH         branche déployée      (défaut : main)
#   DEPLOY_SERVICE        service du bot        (défaut : watcher)
#
# Le script détecte automatiquement le chemin du dépôt et l'utilisateur
# courant ; rien n'est codé en dur.

set -euo pipefail

MODE="${1:-systemd}"
INTERVAL="${DEPLOY_INTERVAL_MIN:-1}"
BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE="${DEPLOY_SERVICE:-watcher}"

cd "$(dirname "$0")/.."
REPO="$(pwd)"
USER_NAME="$(id -un)"
DEPLOY="${REPO}/scripts/deploy.sh"

if [ ! -x "$DEPLOY" ]; then
    echo "Erreur : $DEPLOY introuvable ou non exécutable." >&2
    exit 1
fi

log() { printf '[install-autodeploy] %s\n' "$*"; }

case "$MODE" in
  systemd)
    command -v systemctl >/dev/null 2>&1 || {
        echo "systemctl absent — utilise le mode cron." >&2; exit 1; }

    SVC=/etc/systemd/system/watcher-deploy.service
    TMR=/etc/systemd/system/watcher-deploy.timer

    log "Installation des unités systemd (sudo requis)."
    sed -e "s|__REPO__|${REPO}|g" -e "s|__USER__|${USER_NAME}|g" \
        -e "s|DEPLOY_BRANCH=main|DEPLOY_BRANCH=${BRANCH}|" \
        -e "s|DEPLOY_SERVICE=watcher|DEPLOY_SERVICE=${SERVICE}|" \
        "${REPO}/scripts/watcher-deploy.service" | sudo tee "$SVC" >/dev/null

    sed -e "s|OnUnitActiveSec=1min|OnUnitActiveSec=${INTERVAL}min|" \
        "${REPO}/scripts/watcher-deploy.timer" | sudo tee "$TMR" >/dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable --now watcher-deploy.timer
    log "Timer actif : déploiement vérifié toutes les ${INTERVAL} min."
    log "Suivi : journalctl -u watcher-deploy.service -f"
    ;;

  cron)
    command -v crontab >/dev/null 2>&1 || {
        echo "crontab absent — utilise le mode systemd." >&2; exit 1; }

    if [ "$INTERVAL" -le 1 ]; then SPEC="* * * * *"; else SPEC="*/${INTERVAL} * * * *"; fi
    MARKER="# watcher-autodeploy"
    LINE="${SPEC} cd ${REPO} && DEPLOY_BRANCH=${BRANCH} DEPLOY_SERVICE=${SERVICE} ${DEPLOY} >> ${REPO}/logs/deploy.log 2>&1 ${MARKER}"

    mkdir -p "${REPO}/logs"
    # Remplace une éventuelle entrée précédente (idempotent).
    ( crontab -l 2>/dev/null | grep -v -F "$MARKER" || true; echo "$LINE" ) | crontab -
    log "Entrée cron installée (toutes les ${INTERVAL} min) pour ${USER_NAME}."
    log "Vérifie : crontab -l"
    ;;

  *)
    echo "Mode inconnu : $MODE (attendu : systemd | cron)." >&2
    exit 1
    ;;
esac

log "Le service '${SERVICE}' doit pouvoir être redémarré sans mot de passe :"
log "  echo '${USER_NAME} ALL=(root) NOPASSWD: /usr/bin/systemctl restart ${SERVICE}' | sudo tee /etc/sudoers.d/watcher-deploy"
