# Audit de fonctionnalité — Watcher

Audit de l'état de `main` : test des commandes, ergonomie (user‑friendly),
gestion d'erreurs, journalisation interne, rangement des cogs et
organisation du dépôt.

Échelle : 🟢 conforme · 🟡 amélioration mineure · 🟠 à corriger.

---

## 1. Résumé

**53 commandes** chargées sans erreur (54 cogs). L'ensemble est cohérent et
fonctionnel : commandes hybrides pour le public, owner en préfixe seul,
i18n fr/en complet, gestion d'erreurs centralisée et conviviale,
journalisation triée. Aucun défaut bloquant. Quelques améliorations
mineures listées en §7.

## 2. Commandes (test d'introspection)

- **Descriptions** : toutes les commandes ont une description ; toutes les
  commandes publiques ont leur clé i18n `cmddesc.<nom>` (rendu du help
  traduit fr/en). 🟢
- **Help paginé** : 5 pages (une par catégorie), aucun champ d'embed ne
  dépasse la limite Discord de 1024 caractères. 🟢
- **Propositions d'arguments (slash)** : sélecteur de membre là où c'est
  pertinent (kick, ban, mute, warn, watch, userinfo…), et **choix** pour les
  valeurs finies (on/off des anti‑*, fr/en de `langue`, on/off/status +
  types de `logs`, txt/csv/pdf de `export`). 🟢
- **Owner en préfixe uniquement** : aucune commande d'owner n'est exposée en
  slash. 🟢

## 3. Ergonomie (user‑friendly)

- **Rappels d'usage** : sur argument manquant, message clair avec la
  signature (`❌ Argument manquant. Usage : $kick <member> [raison]`). 🟢
- **Accusés d'action** : confirmations explicites (kick/ban/mute/logs…),
  avec indicateur « MP non délivré » si l'utilisateur a fermé ses MP. 🟢
- **Opérations longues** : `export` et `analyse` signalent l'activité
  (`typing`) ; le PDF est généré hors boucle événementielle (thread). 🟢
- **`logs status`** : vue lisible de l'état de chaque type de log. 🟢

## 4. Gestion d'erreurs

- **Centralisée** (`cogs/errors.py`) : messages traduits pour
  `MissingPermissions`, `BotMissingPermissions`, `NoPrivateMessage`,
  `PrivateMessageOnly`, `CheckFailure`, `MissingRequiredArgument`,
  `Member/UserNotFound`, `BadArgument`, et repli générique. 🟢
- **Libellés de permissions** unifiés via i18n (`dperm.*`), partagés par le
  help et les erreurs. 🟢
- **Rapport aux owners** (`errorreport`) : MP détaillé + traceback sur bug
  inattendu, avec anti‑spam et anti‑récursion. 🟢
- 🟡 Les commandes avec un handler `@cmd.error` **partiel** qui re‑`raise`
  (logs, remindme, say, manage…) court‑circuitent `errors.py` : un type
  d'erreur non prévu par le handler local reste sans message utilisateur
  (l'owner est tout de même notifié). Impact faible (arguments concernés =
  chaînes simples). Piste : repli générique dans les handlers locaux.
- 🟡 `CheckFailure` renvoie `str(error)` brut ; maîtrisé aujourd'hui, mais
  n'afficher que des messages i18n connus serait plus sûr.

## 5. Journalisation interne

- **Console colorée** par niveau (si TTY) + **fichiers triés** (`bot.log`,
  `actions.log`, `errors.log`, rotation quotidienne 30 j). 🟢
- Logger **`action`** dédié au fil des actions (commandes, sanctions,
  arrivées/départs, automod) — 13 points d'appel ; le `LogRecord` n'est
  jamais muté par le formateur couleur (fichiers/tampon web sans ANSI). 🟢
- **Console « live »** du panel web alimentée par le même flux. 🟢

## 6. Rangement des cogs & organisation du dépôt

- **Convention respectée** : un fichier = une commande, sauf regroupements
  liés justifiés (ban/unban, confine/unconfine, mute/unmute,
  warn/unwarn/warns, watch/unwatch/watchlist, addowner/rmowner/owners). 🟢
- **Cogs d'owner** isolés dans `cogs/owner/`. Cogs événementiels dédiés
  (actionlog, errorreport, guildnotify, mention, errors, webpanel). 🟢
- **Séparation nette** : `cogs/` · `utils/` · `web/` · `scripts/` · `docs/`.
  `.env.example`, `requirements.txt`, `.gitignore` présents ; `data/` gardé
  par `.gitkeep`, contenu gitignoré. 🟢
- 🟡 `requirements.txt` épingle `discord.py>=2.3.0` alors que le code cible
  la série 2.7 ; relever le plancher (`>=2.4`) clarifierait le support.

## 7. Améliorations mineures (appliquées)

1. ✅ Handlers d'erreur locaux : repli générique (`error.generic`) — plus
   aucune erreur sans retour utilisateur (11 handlers).
2. ✅ `CheckFailure` : messages i18n uniquement ; type dédié
   `checks.OwnerOnly` pour le message « réservé aux owners » (aucun
   `str(error)` brut relayé).
3. ✅ `requirements.txt` : plancher `discord.py>=2.4.0`.

## 8. Verdict

🟢 **Sain et fonctionnel.** Aucune correction bloquante ; seulement des
améliorations de confort. Le tronc (modération, automod, watch, logs,
export, panel web, i18n) est cohérent et testé.
