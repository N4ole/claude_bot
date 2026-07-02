# Audit — Watcher (bot Discord)

Audit de **fonctionnalité**, **qualité de code** et **sécurité** réalisé sur
l'état de la branche de développement (inclut kick/ban, logs Discord, console
colorée, rapport d'erreurs, rename `Watcher`).

Échelle de sévérité : 🔴 élevée · 🟠 moyenne · 🟡 faible · 🟢 bon point.

---

## 1. Résumé exécutif

Le bot est bien structuré (un fichier par commande, i18n centralisée,
persistance JSON par domaine avec verrous, séparation nette
`cogs`/`utils`/`web`). Aucun défaut **critique** (pas d'`eval`/`exec`,
`subprocess`, désérialisation dangereuse ; secrets lus depuis l'environnement
et jamais journalisés ; endpoints d'administration correctement protégés).

Les points à traiter en priorité concernent le **panel web** :
exposition réseau par défaut, absence de paramètre `state` OAuth, et une
injection HTML (XSS stocké) via les noms de serveurs dans le tableau de bord.

---

## 2. Sécurité

### 🟠 S1 — Panel web exposé sur toutes les interfaces, sans TLS
`config.py` : `WEB_HOST` par défaut `0.0.0.0`, `OAUTH_REDIRECT_URI` en
`http://…`, et le cookie de session est posé **sans l'attribut `Secure`**
(`web_app.py::_set_session`, `httponly`/`SameSite=Lax` seulement).
En déploiement public sans reverse-proxy TLS, le cookie de session et le
`code` OAuth transitent en clair.
- **Reco** : documenter/forcer un reverse-proxy HTTPS ; ajouter `secure=True`
  au cookie quand la requête est en HTTPS ; envisager `WEB_HOST=127.0.0.1`
  par défaut (opt-in explicite pour l'exposition publique).

### 🟠 S2 — Flux OAuth sans paramètre `state` (login CSRF)
`web_app.py::_authorize_url` ne génère pas de `state`, et `/callback` ne le
vérifie pas. Un attaquant peut monter une attaque de type *login CSRF*
(forcer la victime à se connecter sous un compte contrôlé).
- **Reco** : générer un `state` aléatoire (déjà `secrets` importé + `WEB_SECRET`
  disponible), le stocker en cookie court, et le valider dans `/callback`.

### 🟠 S3 — XSS stocké via les noms de serveurs (dashboard)
`web_app.py` (JS) : la console live échappe correctement le contenu
(`ln.msg.replace(/</g,'&lt;')`, 🟢), **mais** les cartes serveur insèrent le
nom via `innerHTML` sans échappement :
`card('<h2>'+g.name+'</h2>…')` (vues owner et admin). Un serveur au nom
piégé (`<img src=x onerror=…>`) exécute du script dans le navigateur de
l'owner/admin qui consulte le panel.
- **Reco** : échapper `g.name` (fonction `esc()` HTML) ou construire le titre
  via `textContent` plutôt que `innerHTML`.

### 🟡 S4 — `errors.py` renvoie `str(error)` des `CheckFailure`
La branche `CheckFailure` renvoie le message brut de l'exception. Nos checks
posent des messages maîtrisés (FR), mais une `CheckFailure` tierce pourrait
divulguer un détail interne.
- **Reco** : n'afficher que des messages i18n connus ; logguer le détail.

### 🟢 Bons points sécurité
- Endpoints `/, /api/control/*, /api/logs` gardés par `_require_owner`
  (session + `guild_ids == "all"`).
- `SameSite=Lax` limite le CSRF sur les POST d'administration.
- Secrets (`DISCORD_TOKEN`, `OAUTH_CLIENT_SECRET`) uniquement via env,
  jamais logués ; `bot.run(..., log_handler=None)`.
- Permissions Discord vérifiées sur les commandes sensibles (`has_permissions`,
  `bot_has_permissions`, `guild_only`) et garde-fous hiérarchie/auto-sanction
  sur kick/ban.

---

## 3. Qualité de code

### 🟡 Q1 — Plusieurs listeners `on_command_error`
`errors.py`, `errorreport.py`, `logs.py` (et complétions dans `actionlog.py`)
écoutent le même événement. C'est volontaire et fonctionnel, mais à
documenter pour éviter des doublons de traitement lors d'évolutions.

### 🟡 Q2 — Duplication des libellés de permissions
`cogs/errors.py::_PERMS` redéfinit des traductions déjà présentes dans
`i18n` (`perm.*`). Source unique souhaitable.

### 🟡 Q3 — Paramètre `type` masquant le built-in
`cogs/logs.py::logs(self, ctx, etat, type)` masque `type()`. Renommer en
`categorie`/`kind` améliorerait la lisibilité.

### 🟡 Q4 — Écritures JSON non atomiques
`storage.py` écrit directement dans le fichier cible. Un crash en cours
d'écriture peut corrompre le JSON.
- **Reco** : écrire dans un fichier temporaire puis `os.replace()` (atomique).

### 🟡 Q5 — Lectures disque répétées
`get_setting`/`_enabled` relisent le fichier à chaque appel (dont sur chaque
commande via le routage des logs). Acceptable à l'échelle actuelle ; un cache
mémoire invalidé à l'écriture serait un plus si le trafic grandit.

### 🟢 Bons points qualité
- Convention « un fichier = une commande » respectée.
- i18n et catégories centralisées (`utils/i18n.py`, `utils/categories.py`).
- Journalisation soignée : le `LogRecord` n'est pas muté par le formateur
  couleur, les fichiers restent sans codes ANSI.
- Verrous (`Lock`) par domaine dans `storage.py`.

---

## 4. Fonctionnalité

### 🟠 F1 — `ban`/`kick` limités aux membres présents
Les deux commandes typent la cible en `discord.Member` : impossible de bannir
par **ID** un utilisateur déjà parti (usage courant de modération).
- **Reco** : accepter `discord.User`/ID (converti), garder `Member` pour les
  contrôles de hiérarchie quand la personne est présente.

### 🟡 F2 — Pas d'`unban` manuel
Seul le ban **temporaire** se lève automatiquement ; aucun moyen de débannir
manuellement via le bot (paire naturelle `ban`/`unban`).

### 🟡 F3 — MP « best-effort » silencieux
Si l'utilisateur a ses MP fermés, kick/ban n'informe pas le modérateur que le
MP n'a pas pu être envoyé. Comportement voulu, mais un indicateur discret
(« MP non délivré ») serait utile.

### 🟡 F4 — Descriptions slash en français uniquement
Les descriptions enregistrées auprès de Discord (UI slash) restent en
français ; seul le rendu du `help` est bilingue. La localisation native des
commandes slash (`app_commands` locale) pourrait être envisagée.

### 🟢 Bons points fonctionnels
- Bans temporaires **persistés** et repris au démarrage (`on_ready`).
- MP **avant** sanction (le bot ne partage plus de serveur ensuite).
- Logs Discord par type, catégorie masquée, activation indépendante.

---

## 5. Plan d'action recommandé (par priorité)

1. **S3** — échapper `g.name` dans le dashboard (rapide, supprime le XSS).
2. **S1/S2** — cookie `Secure` conditionnel + `state` OAuth ; défaut
   `WEB_HOST=127.0.0.1` documenté.
3. **F1** — permettre le ban par ID (User), + **F2** commande `unban`.
4. **Q4** — écritures JSON atomiques (`os.replace`).
5. **Q1–Q3, Q5, S4, F3–F4** — nettoyages de fond au fil de l'eau.

> Aucun correctif n'est appliqué dans cette PR : ce document est un état des
> lieux. Les corrections seront traitées dans des PR dédiées et revues.
