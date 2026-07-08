# CLAUDE.md — Watcher (bot Discord)

Guide d'orientation pour les futures instances de Claude travaillant sur ce
dépôt. À lire **en premier**.

> ⚠️ Ce dépôt s'appelait `claude_bot` et a été renommé **`Watcher`** (voir
> « Renommage » plus bas). Il n'a **aucun** rapport avec un projet de
> benchmark de bases de données.

---

## 1. Résumé du projet

**Watcher** est un bot Discord de **modération et d'utilitaires**, en Python
(`discord.py`), entièrement **bilingue** (français par défaut, anglais). Il
fournit : modération (kick/ban/mute/warn/confine + modération vocale), notes de
dossier, automodération (anti-raid, anti-spam, anti-pub, anti-insulte,
anti-caps/emoji, anti-bot), surveillance d'utilisateurs (`watch`), logs Discord
par catégorie (dont la modération faite hors commande), messages de
bienvenue/au revoir, giveaways, tickets, export du journal de modération, un
**panel web** d'administration (OAuth2 Discord), une gestion d'**owners du
bot** (dont blacklist de serveurs), et un système de **déploiement
automatique** depuis GitHub.

- **Version actuelle : `0.20` — en bêta** (`config.VERSION` / `config.BETA`).
- Commandes **hybrides** (préfixe **personnalisable par serveur** — commande
  `prefixe`, défaut `!` via .env, persisté dans guild_settings — **et** slash
  `/`) pour le public ;
  commandes d'**owner en préfixe uniquement**.

## 2. Stack & outils

- **Python 3.11**, `discord.py` 2.7.x.
- **Web** : `aiohttp` (panel + OAuth2 Discord), thème néon (HTML/CSS/JS
  inline, Chart.js côté client).
- **Graphiques** : `matplotlib` (backend Agg) pour la commande `analyse`.
- **Persistance** : fichiers **JSON** par domaine (pas de base de données),
  un `Lock` par fichier, écritures **atomiques** (`os.replace`).
- **Config** : `.env` via `python-dotenv` (`config.py`).
- **Déploiement** : `scripts/deploy.sh` + unités systemd + installeur
  (`scripts/install-autodeploy.sh`).
- **Docs générées** : `scripts/gen_docs.py`.

## 3. Architecture

```
main.py            Point d'entrée : setup_logging() puis bot.run().
bot.py             Classe Watcher(commands.Bot) : intents, chargement auto
                   des cogs, sync slash, on_error global. Statut Discord géré
                   par le cog `presence` (rotation).
config.py          Env (.env) : TOKEN, PREFIX, OWNER_ID, GUILD_ID, REPO_URL,
                   SUPPORT_SERVER, OAUTH_*, WEB_*, VERSION, BETA.
cogs/              Un fichier = une commande (voir convention).
cogs/owner/        Commandes réservées aux owners du bot (préfixe seul,
                   masquées du help public).
utils/             Modules partagés (voir §5).
web/               Panel aiohttp + OAuth2 + console live.
scripts/           deploy.sh, install-autodeploy.sh, unités systemd, gen_docs.
docs/              AUDIT.md, DEPLOY.md, OAUTH_SETUP.md + docs générées.
data/              JSON runtime (gitignored : data/*.json).
logs/              Journaux fichiers (gitignored).
```

### Convention cogs (IMPORTANT)

**Un fichier = une commande**, sauf commandes directement liées qui vont
ensemble (`mute`/`unmute`, `ban`/`unban`, `confine`/`unconfine`,
`warn`/`unwarn`, `watch`/`unwatch`). Chargement **récursif** depuis `cogs/`
(fichiers commençant par `_` ignorés). Cogs « événementiels » sans commande :
`actionlog`, `errorreport`, `guildnotify`, `mention`, `errors`, `webpanel`.

## 4. Sous-systèmes clés

- **Modération** : `kick` (raison + MP à l'utilisateur), `ban` (raison +
  durée optionnelle → ban temporaire persisté, déban auto + MP + invitation ;
  **ban par ID** possible via `discord.User`, donc même hors serveur),
  `unban <id>`, `mute`/`unmute` (timeout Discord), `warn` (escalade 1→5 :
  avert. → mute 5 min → mute 1 h → confinement 1 semaine → ban),
  `confine`/`unconfine`, `clear`. Garde-fous : pas d'auto-sanction, respect
  de la hiérarchie des rôles (l'owner du serveur outrepasse).
- **Modération vocale** : `mutemicro`/`unmutemicro` (server mute),
  `mutecasque`/`unmutecasque` (server deafen), `move` (déplacement vocal).
  Permissions dédiées dans `checks.py` (`mute_voice_perms`,
  `deafen_voice_perms`, `move_perms`) ; actions consignées au dossier.
- **Notes de dossier** : `note <membre> <texte>` / `delnote <membre> <n°>`
  (admin) ajoutent/retirent des notes libres, affichées par `userstatus`
  (persistées dans `notes.json`).
- **Automodération** : `antibot`, `antiraid` (captcha à l'arrivée),
  `antipub`, `antispam`, `antiinsulte`, anti-caps, anti-emoji. **Les admins
  sont exemptés** (choix produit).
- **Watch** : `watch <user>` copie l'activité d'un membre dans un salon dédié
  (messages, éditions, suppressions, vocal, réactions, pseudo/statut).
- **Logs Discord** : `logs <on|off> <catégorie>` (admin, `logs status` pour
  l'état). Crée une catégorie `logs` (masquée) + un salon par type activé
  (types = catégories du help). Consigne chaque commande de la catégorie
  (qui/où/via/args) et les échecs. La résolution du salon est factorisée dans
  `utils/logchannels.py` (source unique, réutilisée hors de la commande).
- **Logs de modération hors commande** (`modevents`) : suppression de message
  par un modérateur (clic droit), ban/déban/kick faits directement dans
  Discord → consignés dans le salon de logs `mod`. Déduplication via les logs
  d'audit (les actions du bot ne sont pas re-journalisées ; nécessite la
  permission « Voir les logs d'audit »). L'anti-bot y journalise aussi ses
  expulsions.
- **Export** : `export <txt|csv|pdf> [période]` (propriétaire du serveur) —
  exporte le journal de modération sur une période.
- **Bienvenue / au revoir** (`welcome`, admin) : groupe `bienvenue` (salon,
  message, aurevoir, mp on/off, mpmessage, config). Messages d'arrivée/départ
  dans un salon + **MP de bienvenue** optionnel, tous personnalisables
  (placeholders `{user}`/`{name}`/`{server}`/`{count}`).
- **Giveaways** (`giveaway`, admin) : `giveaway <durée> <gagnants> <prix>`
  (réaction 🎉), `gend` (fin anticipée), `greroll` (nouveau tirage). Persistés
  (`giveaways.json`) et repris au démarrage (`on_ready`).
- **Tickets** (`ticket`, admin) : `ticket <salon> <message>` poste un panneau
  avec un **bouton persistant** (`discord.ui.View`, `custom_id` stable,
  ré-enregistré via `bot.add_view` au chargement du cog). Un clic crée un
  salon privé `ticket-<n°>` (catégorie `tickets`, visible du membre + admins) ;
  numérotation via `storage.next_ticket_number`. `closeticket` retire l'accès
  du membre et renomme le salon `closed-<n°>`.
- **Owners du bot** (`cogs/owner/`, **préfixe uniquement**) :
  `addowner`/`rmowner`/`owners` (manage), `serveurs`, `invite`, `respond`
  (MP à un propriétaire de serveur, ou `all` pour une annonce), `helpowner`,
  `central`, `reload`/`shutdown`/`say`, `leave <id>` (quitter un serveur),
  `banserv`/`unbanserv`/`banservs` (**blacklist de serveurs** : départ auto +
  MP au proprio avec lien de support + alerte owners). Réservés via
  `checks.is_owner()`, utilisables aussi en MP.
- **Notifications owners** : `guildnotify` envoie un MP à tous les owners
  quand le bot **rejoint/quitte** un serveur (infos serveur + total).
- **Rapport d'erreurs** : `errorreport` envoie un MP détaillé aux owners sur
  erreur inattendue (commande ou événement, via `Watcher.on_error`), avec
  traceback (jointe si longue), anti-spam et anti-récursion.
- **Contact** : `contactowner` (propriétaire d'un serveur → owners du bot).

## 5. Modules `utils/`

- `storage.py` — persistance JSON par domaine (réglages, warns, watched,
  confinements, **tempbans**, modlog, **notes**, reminders, **giveaways**,
  **blacklist de serveurs**, owners ; compteur de tickets dans les réglages).
  **Écritures atomiques** (`_atomic_dump`), **cache mémoire des réglages**
  (invalidé à l'écriture), un `Lock` par fichier.
- `i18n.py` — `t(source, key, **kwargs)` résout la langue via `source`
  (Context/guild/id → réglage `lang`, français par défaut). Grand `_CATALOG`
  fr/en, `EIGHTBALL`, `get_lang`. Descriptions du help via `cmddesc.<nom>`.
- `categories.py` — **source unique** du mapping cog → catégorie
  (`cat.*`) + permissions, partagé par le **help** ET les **logs**
  (`TYPE_TO_CAT` / `CAT_TO_TYPE` / `resolve_type`).
- `logchannels.py` — résolution du salon de logs d'un type (`log_channel`),
  **source unique** partagée par `logs`, `modevents` et l'anti-bot.
- `checks.py` — **SOURCE UNIQUE de toutes les vérifications de
  permissions** (voir §5 bis). Décorateurs : `admin()`, `kick_perms()`,
  `ban_perms()`, `manage_messages()`, `mute_voice_perms()`,
  `deafen_voice_perms()`, `move_perms()`, `server_owner()`, `is_owner()`.
  Prédicats : `is_admin(member)`, `can_act_on(author, target)`,
  `is_owner_or_server_owner(ctx)`, `is_owner_id`, `all_owner_ids()`.
  Exceptions dédiées : `OwnerOnly`, `ServerOwnerOnly` (affichées en i18n
  par `cogs/errors.py`).
- `duration.py` — `parse_duration("1h30m")` → timedelta ; `human(delta)`.
- `automod.py` — escalade partagée caps/emoji. `badwords.py` — dictionnaire
  multilingue anti-insulte. `analytics.py` — séries pour `analyse`.
- `logsetup.py` — **console colorée** (ANSI par niveau, seulement si TTY ; le
  `LogRecord` n'est jamais muté) + **fichiers triés** (`bot.log`,
  `actions.log`, `errors.log`, rotation quotidienne, 30 jours).

### 5 bis. Permissions centralisées (IMPORTANT)

**Ne jamais réécrire de vérification de permission dans un cog** : tout vit
dans `utils/checks.py` (un fichier = cet élément), on ne fait qu'appeler la
fonction. Concrètement :

```python
from utils import checks

@commands.hybrid_command(...)
@checks.admin()                    # au lieu de guild_only + has_permissions
async def macommande(...):
    if not checks.can_act_on(ctx.author, member):   # hiérarchie kick/ban
        ...

# Dans un listener (automod) :
if checks.is_admin(message.author):   # exemption admins
    return
```

- Décorateurs : `admin()`, `kick_perms()`, `ban_perms()`,
  `manage_messages()`, `mute_voice_perms()`, `deafen_voice_perms()`,
  `move_perms()`, `server_owner()`, `is_owner()` — ils incluent déjà
  `guild_only` et les permissions bot quand pertinent.
- Prédicats : `is_admin(member)` (exemption automod),
  `can_act_on(author, target)` (hiérarchie des rôles, owner du serveur
  outrepasse), `is_owner_or_server_owner(ctx)` (export…),
  `is_owner_id(user_id)` (web, listeners).
- Les refus lèvent des exceptions typées (`OwnerOnly`, `ServerOwnerOnly`,
  `MissingPermissions`…) traduites par le gestionnaire global
  (`cogs/errors.py`) — aucun message de permission n'est écrit dans les cogs.
- **Ajouter une nouvelle règle de permission = ajouter UNE fonction dans
  `utils/checks.py`**, jamais du code inline dans un cog.

## 6. Web (`web/`)

- `web_app.py` — app aiohttp : OAuth2 Discord (**avec `state` anti-CSRF**),
  sessions en mémoire (cookie httponly + **`Secure` conditionnel** en HTTPS),
  page de login (consentement cookies **bloquant**), dashboard owner à 3
  pages (Général / Analytics / Live), pages légales bilingues. Les noms de
  serveurs sont **échappés** (`esc()`) à l'affichage (anti-XSS).
- `logbuffer.py` — tampon circulaire des logs pour la console « live ».
- `prefs.py` — langue par **compte** web. `stats.py` — instantanés/historique.
- **Écoute sur `127.0.0.1` par défaut** (`WEB_HOST`) : exposition publique
  volontaire (derrière un reverse-proxy HTTPS).

## 7. Internationalisation

Tout texte affiché passe par `t(source, "clef", **kwargs)`. Ajouter une
chaîne = entrée `{"fr": ..., "en": ...}` dans `_CATALOG` (`utils/i18n.py`).
Langue résolue **par serveur** (réglage `lang`) et **par compte** côté web.
Les descriptions de commandes du help sont traduites via `cmddesc.<nom>`
(repli sur la description du décorateur).

## 8. Journalisation

`utils/logsetup.py`, branché dans `main.setup_logging()` :
- **Console colorée** par niveau (DEBUG cyan, INFO vert, WARNING jaune,
  ERROR rouge, CRITICAL blanc/rouge).
- **Fichiers triés** (`logs/`, rotation quotidienne) : `bot.log` (tout),
  `actions.log` (logger `action`), `errors.log` (WARNING+).
- Le logger nommé `action` est le fil des « actions » du bot.

## 9. Déploiement automatique

- `scripts/deploy.sh` — récupère la branche suivie, **remplace le code local
  par GitHub** (`git reset --hard`, les fichiers gitignorés `data/`, `.env`,
  `logs/` sont **préservés**), réinstalle les dépendances si
  `requirements.txt` a changé, redémarre le service. Idempotent + verrou.
- `scripts/install-autodeploy.sh` — installe le **lancement périodique** en
  une commande (timer systemd par défaut, ou cron), chemins auto-détectés.
- `scripts/watcher-deploy.{service,timer}` + `docs/DEPLOY.md`.
> Résultat : chaque push GitHub se déploie tout seul (redémarrage uniquement
> s'il y a de nouveaux commits).

## 10. Décisions techniques

- **Commandes hybrides** pour le public (préfixe + slash d'un tenant) ;
  **owner en préfixe seul** (choix produit).
- **Persistance JSON** simple + verrous + écritures atomiques (échelle du
  bot ; pas de base de données).
- **i18n et catégories centralisées** (une seule source de vérité).
- **MP avant sanction** (kick/ban) : une fois exclu, le bot ne partage plus
  de serveur avec l'utilisateur.
- **Bans temporaires / confinements persistés** et repris au démarrage
  (`on_ready`).
- **Durcissement web** (audit `docs/AUDIT.md`) : `state` OAuth, cookie
  `Secure`, échappement XSS, écoute locale par défaut.

## 11. Workflow Git

- Développement sur des **branches dédiées** ; **jamais** de push direct sur
  `main` sans autorisation. Après push, **PR** (draft, passée « ready » sur
  demande) puis fusion dans `main`.
- Trailer de commit :
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- `data/*.json` et `logs/` sont **gitignored**.
- **Ne jamais** mettre l'identifiant du modèle dans un commit / PR / code.

### Renommage `ClaudeBot` → `Watcher`

Dépôt renommé `Watcher` sur GitHub, code rebrandé (classe `ClaudeBot` →
`Watcher`, imports, tous les textes affichés).
**Sandbox** : le proxy git est verrouillé sur l'ancien chemin
`N4ole/claude_bot` ; pointer le remote vers `…/Watcher` renvoie **403**.
→ **Garder** le remote sur `…/git/N4ole/claude_bot` : GitHub redirige
automatiquement vers `Watcher`, fetch/push fonctionnent. Sur une machine
locale (hors sandbox) : `git remote set-url origin
https://github.com/N4ole/Watcher.git`.

## 12. État actuel

- Tronc complet et fusionné sur `main` : modération (dont kick/ban/unban,
  ban par ID), automod, watch, logs Discord, panel web durci, i18n fr/en,
  console colorée + logs fichiers, rapport d'erreurs, notifications owners
  join/leave, déploiement auto.
- **Version `0.20` (bêta)**, affichée dans `botinfo`, `status`, `central` et
  le statut Discord.
- Le repo n'a **pas** de checks CI configurés.

## 13. Prochaines étapes possibles

- Améliorations mineures issues de l'audit fonctionnel (`docs/AUDIT.md`) :
  repli générique dans les handlers d'erreur locaux, message i18n pour
  `CheckFailure`, relever le plancher `discord.py` dans `requirements.txt`.
- Localisation native des descriptions slash (`app_commands` locale).
- Étendre les logs Discord aux événements non-commandes (automod,
  arrivées/départs) si souhaité.
- Régénérer la documentation (`python scripts/gen_docs.py`) après ajout de
  commandes.
- Basculer `config.BETA = False` à la sortie stable (retire la mention bêta
  partout).
