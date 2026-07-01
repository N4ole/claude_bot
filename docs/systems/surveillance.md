# Système de surveillance (watch)

Journalise toute l'activité d'un utilisateur dans un salon dédié.

## Commandes
- `§watch <membre>` — active la surveillance
- `§unwatch <membre>` — l'arrête (le salon de log est conservé)
- `§watchlist` — liste les utilisateurs surveillés

Réservées aux **administrateurs**.

## Fonctionnement
`watch` crée la catégorie `WATCHED USER` et un salon privé `<user>-watched`
(visible des administrateurs et du bot) où sont recopiés :

- 📨 messages **envoyés** (contenu, salon, lien, pièces jointes) ;
- ✏️ messages **modifiés** (avant / après) ;
- 🗑️ messages **supprimés** ;
- 👍/👎 **réactions** ajoutées / retirées ;
- 🏷️ changements de **pseudo** ;
- 🟢 changements de **statut** ;
- 🔊 activité **vocale** : connexion, déconnexion (heure de sortie + durée),
  changement de salon.

## Persistance
Les cibles surveillées sont conservées dans `data/watched.json` (survit aux
redémarrages).

## Intents requis
`message_content`, `members`, `voice_states`, `presences`.
