# Système de rappels (remindme)

## Commande
- `§remindme <message> <temps>` — envoie un rappel en **message privé** après
  le délai indiqué.

Accessible à tous.

## Format du temps
Court et combinable : `30s`, `5m`, `2h`, `1d` (ou `1j`), `1h30m`… (voir
[`utils/duration.py`](../../utils/duration.py)).

## Fonctionnement
1. Le rappel est enregistré dans `data/reminders.json` avec son échéance.
2. Une tâche attend l'échéance puis envoie le message en MP (repli sur le salon
   d'origine si le MP est fermé), puis supprime l'entrée.
3. Au démarrage, tous les rappels en attente sont **repris automatiquement**.

> En slash, `message` et `temps` sont deux champs séparés ; en préfixe, mettez
> le message entre guillemets s'il contient des espaces.
