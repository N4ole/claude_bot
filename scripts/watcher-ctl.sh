#!/usr/bin/env bash
#
# Démarre/arrête/redémarre Watcher lancé comme simple processus Python
# (SANS systemd), avec relance automatique en cas de plantage.
#
# Usage :
#   scripts/watcher-ctl.sh start|stop|restart|status
#
# Variables d'environnement :
#   DEPLOY_PYTHON   interpréteur Python (défaut : python3)
#   WATCHER_LOG     fichier de sortie du bot (défaut : logs/runtime.log)
#
# Utilisé automatiquement par scripts/deploy.sh quand aucun service systemd
# n'est configuré : voir docs/DEPLOY.md.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"
PYTHON="${DEPLOY_PYTHON:-python3}"
PIDFILE="${REPO_ROOT}/.watcher.pid"
STOPFLAG="${PIDFILE}.stop"
LOGFILE="${WATCHER_LOG:-${REPO_ROOT}/logs/runtime.log}"
mkdir -p "$(dirname "$LOGFILE")"

log() { printf '[watcher-ctl] %s\n' "$*"; }

# PID de la boucle de relance, si elle tourne encore (nettoie le fichier
# sinon, pour ne pas laisser traîner un PID mort).
running_pid() {
    if [ -f "$PIDFILE" ]; then
        local pid
        pid="$(cat "$PIDFILE" 2>/dev/null || true)"
        if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    return 1
}

do_start() {
    if pid="$(running_pid)"; then
        log "Déjà lancé (pid boucle $pid)."
        return 0
    fi
    rm -f "$STOPFLAG"
    log "Démarrage (${PYTHON} main.py), sortie -> ${LOGFILE}."
    # Boucle de relance : si main.py plante ou s'arrête, il est relancé après
    # un court délai — sauf si un arrêt volontaire a été demandé (STOPFLAG).
    # `"$0" main.py` dans le bloc -c : $0 y vaut "$PYTHON" (passé en argument
    # positionnel après le script), donc équivaut à `"$PYTHON" main.py`.
    nohup bash -c '
        while true; do
            "$0" main.py
            code=$?
            if [ -f "'"$STOPFLAG"'" ]; then
                break
            fi
            printf "[watcher-ctl] main.py terminé (code %s) — relance dans 2s.\n" "$code"
            sleep 2
        done
    ' "$PYTHON" >>"$LOGFILE" 2>&1 &
    disown
    echo $! > "$PIDFILE"
    log "Démarré (pid boucle $(cat "$PIDFILE"))."
}

do_stop() {
    if pid="$(running_pid)"; then
        log "Arrêt (pid boucle $pid)."
        # Le flag est posé AVANT de tuer le process en cours : si main.py
        # est tué pendant qu'il tourne, la boucle voit le flag et s'arrête
        # au lieu de relancer une nouvelle instance (pas de course).
        touch "$STOPFLAG"
        pkill -TERM -P "$pid" 2>/dev/null || true
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        if kill -0 "$pid" 2>/dev/null; then
            log "Ne répond pas à TERM après 10s — arrêt forcé (KILL)."
            pkill -KILL -P "$pid" 2>/dev/null || true
            kill -KILL "$pid" 2>/dev/null || true
        fi
        rm -f "$PIDFILE" "$STOPFLAG"
        log "Arrêté."
    else
        log "Pas de processus en cours."
        rm -f "$PIDFILE" "$STOPFLAG"
    fi
}

case "${1:-}" in
    start) do_start ;;
    stop) do_stop ;;
    restart) do_stop; do_start ;;
    status)
        if pid="$(running_pid)"; then
            log "En cours (pid boucle $pid)."
        else
            log "Arrêté."
            exit 1
        fi
        ;;
    *)
        echo "Usage : $0 start|stop|restart|status" >&2
        exit 1
        ;;
esac
