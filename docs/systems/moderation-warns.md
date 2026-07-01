# Système d'avertissements (warns)

Système de sanctions **progressives** : chaque avertissement fait monter d'un
niveau et applique automatiquement une sanction.

## Commandes
- `§warn <membre>` — avertit (monte d'un niveau)
- `§unwarn <membre>` — retire un avertissement et lève les sanctions temporaires
- `§warns <membre>` — affiche le nombre d'avertissements

Réservées aux **administrateurs**.

## Barème
Un rôle `Warn N` (sans permission) reflète le niveau courant et **remplace** le
précédent.

| Niveau | Sanction |
|--------|----------|
| 1 | Simple avertissement |
| 2 | Mute (timeout) 5 minutes |
| 3 | Mute (timeout) 1 heure |
| 4 | Confinement pendant une semaine (voir *Confinement*) |
| 5 | Bannissement permanent |

## Persistance
- Compteur par serveur/membre : `data/warns.json`.
- Chaque action est aussi enregistrée dans le **journal de modération**
  (`data/modlog.json`), consultable via `§userstatus`.

## Permissions requises pour le bot
Gérer les rôles, Exclure des membres (timeout), Bannir des membres — avec un
rôle placé au-dessus des membres visés.
