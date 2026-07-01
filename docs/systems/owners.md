# Système d'owners du bot

Gère les propriétaires du bot (différents des administrateurs de serveur).

## Owner principal
Défini par `OWNER_ID` dans le `.env`. Il a tous les droits et **ne peut pas**
être retiré.

## Owners additionnels
Gérés dynamiquement, stockés dans `data/owners.json`.

## Commandes (réservées aux owners)
- `§addowner <user>` / `§rmowner <user>` / `§owners` — gestion des owners
- `§reload [cog]` — recharge un cog à chaud (ou `all`)
- `§shutdown` — éteint le bot
- `§say <message>` — fait parler le bot
- `§serveurs` — détaille chaque serveur du bot (une page par serveur)
- `§invite <serverid>` — génère une invitation vers un serveur du bot
- `§helpowner` — liste les commandes d'owner (préfixe uniquement)

## Rôle automatique
Quand un owner rejoint un serveur où le bot est présent, il reçoit
automatiquement un rôle `owner-claudebot` (sans permission).

## Commandes en message privé
Les owners peuvent utiliser les commandes du bot en **MP** (les commandes
nécessitant un serveur restent réservées aux serveurs). En MP, les commandes
des non-owners sont ignorées.

## Vérification réutilisable
Le prédicat [`checks.is_owner`](../../utils/checks.py) permet de réserver
n'importe quelle commande aux owners.
