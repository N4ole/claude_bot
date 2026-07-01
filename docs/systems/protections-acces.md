# Système de protection d'accès (anti-bot / anti-raid)

Protège l'entrée du serveur. Réglages activables par serveur, visibles via
`§protections`.

## Anti-bot — `§antibot <on/off>`
Quand activé, tout **bot** qui rejoint le serveur est automatiquement expulsé.

## Anti-raid — `§antiraid <on/off>`
Quand activé, chaque nouveau membre doit valider un **captcha** avant d'accéder
au serveur (sans API externe) :

1. Création (si besoin) d'un rôle `Non vérifié` (masque toutes les catégories)
   et d'un salon `vérification`.
2. Le nouveau membre reçoit le rôle et doit **recopier un code** (6 caractères
   sans caractères ambigus) dans le salon de vérification.
3. Bon code → le rôle est retiré (accès débloqué). Après 3 échecs ou 5 minutes
   → expulsion.

> La vérification en cours est gérée en mémoire : un redémarrage laisse le
> membre « Non vérifié » (un administrateur peut retirer le rôle).

## Persistance
Réglages on/off dans `data/guild_settings.json`.

## Permissions requises pour le bot
Gérer les rôles, Gérer les salons, Expulser des membres.
