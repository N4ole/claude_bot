# Système de confinement

Isole un utilisateur dans un salon privé et lui retire l'accès au reste du
serveur.

## Commandes
- `§confine <membre>` — confine l'utilisateur
- `§unconfine <membre>` — le libère

Réservées aux **administrateurs**.

## Fonctionnement
1. Création (si besoin) de la catégorie `confinement` et d'un salon
   `confin-<user>` visible uniquement par l'utilisateur et les administrateurs.
2. L'accès aux autres catégories/salons est refusé au membre
   (`view_channel` = false). Les salons synchronisés héritent du refus.
3. `unconfine` restaure l'accès et supprime le salon (et la catégorie si vide).

Le salon est retrouvé via un marqueur `id: <user_id>` dans son sujet, ce qui
rend `unconfine` fiable même après un changement de pseudo.

## Confinement temporisé
Le **warn niveau 4** confine pour **une semaine**. L'échéance est persistée dans
`data/confinements.json` et la libération est **reprise automatiquement au
démarrage** (immédiate si l'échéance est déjà passée).

## Permission requise pour le bot
Gérer les salons.
