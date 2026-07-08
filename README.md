# Watcher

Bot Discord de **modération et d'utilitaires** en Python (`discord.py`),
**bilingue** (français par défaut, anglais). Il supporte à la fois les
**commandes préfixe** (`!` par défaut, **personnalisable par serveur** via la
commande `prefixe`) et les **commandes slash** (`/`), avec une architecture
multi-fichiers (un fichier par commande).

- **Version : `0.20` (bêta).**
- Commandes publiques **hybrides** (préfixe + slash) ; commandes d'**owner du
  bot** en **préfixe uniquement**.

## Sommaire des fonctionnalités

- **Modération** : `kick`, `ban`/`unban` (dont ban temporaire et ban par ID),
  `mute`/`unmute` (timeout), `warn` (escalade 1→5), `confine`/`unconfine`,
  `clear`.
- **Modération vocale** : `mutemicro`/`unmutemicro` (couper le micro),
  `mutecasque`/`unmutecasque` (couper le son), `move` (déplacer en vocal).
- **Dossier utilisateur** : `userstatus` (historique des sanctions), `note` /
  `delnote` (notes libres).
- **Automodération** : anti-bot, anti-raid (captcha), anti-pub, anti-spam,
  anti-insulte, anti-majuscules, anti-emojis (les admins sont exemptés).
- **Surveillance** : `watch` recopie l'activité d'un membre dans un salon dédié.
- **Logs Discord** : `logs` (par catégorie) + journalisation de la modération
  **faite hors commande** (suppression de message, ban/kick manuels…).
- **Bienvenue / au revoir** : messages d'arrivée/départ + **MP de bienvenue**,
  tous personnalisables.
- **Giveaways** : `giveaway`, `gend`, `greroll` (réaction 🎉, persistés).
- **Tickets** : panneau à **bouton persistant** créant des salons privés.
- **Export** : journal de modération en `txt` / `csv` / `pdf`.
- **Panel web** d'administration (OAuth2 Discord, thème néon, console live).
- **Owners du bot** : gestion des owners, tableau de bord, blacklist de
  serveurs, quitter un serveur à distance…
- **Déploiement automatique** depuis GitHub (`scripts/deploy.sh`).

## Structure

```
Watcher/
├── main.py          # Point d'entrée : lance le bot
├── bot.py           # Classe du bot + chargement automatique des cogs
├── config.py        # Configuration (token, préfixe, owner, OAuth, support…)
├── requirements.txt
├── .env.example     # Modèle de configuration
├── utils/           # Modules communs
│   ├── storage.py       # Persistance (JSON par domaine, écritures atomiques)
│   ├── i18n.py          # Catalogue de traductions fr/en (t(ctx, clé))
│   ├── checks.py        # Vérifications de permissions (source unique)
│   ├── categories.py    # Mapping cog → catégorie (help ET logs)
│   ├── logchannels.py   # Résolution des salons de logs (source unique)
│   ├── duration.py      # parse_duration("1h30m") / human(delta)
│   ├── automod.py       # Escalade anti-caps / anti-emojis
│   ├── badwords.py      # Dictionnaire anti-insulte
│   ├── analytics.py     # Séries temporelles (commande analyse)
│   └── logsetup.py      # Console colorée + fichiers de logs
├── web/             # Panel web (aiohttp + OAuth2 Discord)
├── scripts/         # deploy.sh, install-autodeploy.sh, unités systemd, gen_docs
├── docs/            # Documentation (guides + docs générées)
├── data/            # Données runtime (JSON, ignoré par git)
└── cogs/            # Un fichier par commande / fonctionnalité
    └── owner/           # Commandes réservées aux owners du bot
```

Les cogs sont chargés **récursivement** : ajouter un fichier dans `cogs/` **ou**
dans un sous-dossier (comme `cogs/owner/`) suffit pour ajouter une commande.

## Documentation

Documentation détaillée dans [`docs/`](docs/README.md), sur trois axes :
- **Par commande** — [`docs/commands/`](docs/commands/README.md) (une fiche par
  commande, générée automatiquement)
- **Par catégorie** — [`docs/categories/`](docs/categories/README.md)
- **Par système** — [`docs/systems/`](docs/systems/README.md)

Régénérer les fiches par commande/catégorie après un changement :
`python -m scripts.gen_docs`.

Le bot est **bilingue** : `langue <fr/en>` change la langue **par serveur** ;
les messages passent par le catalogue centralisé
[`utils/i18n.py`](utils/i18n.py). Chaque commande publique utilise
`@commands.hybrid_command` (disponible en `!ping` **et** `/ping`). Le préfixe
est propre à chaque serveur (`prefixe <nouveau>` / `prefixe reset`) ; la
mention du bot reste toujours utilisable en secours. Les slash sont
synchronisées sur le serveur de dev (`GUILD_ID`, instantané) **et**
globalement. Mentionner le bot (`@Watcher` seul) affiche un message de
présentation.

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
```

Renseignez votre `DISCORD_TOKEN` dans `.env`. Dans le portail développeur
Discord, activez les intents **MESSAGE CONTENT**, **SERVER MEMBERS** et
**PRESENCE INTENT**. Donnez au bot les permissions nécessaires à ses actions
(dont **Gérer les salons**, **Gérer les rôles**, et **Voir les logs d'audit**
pour la journalisation de la modération hors commande).

## Lancement

```bash
python main.py
```

## Configuration (`.env`)

| Variable          | Description                                                       | Défaut |
|-------------------|------------------------------------------------------------------|--------|
| `DISCORD_TOKEN`   | Token du bot (obligatoire)                                        | —      |
| `COMMAND_PREFIX`  | Préfixe **par défaut** (chaque serveur peut le changer)          | `!`    |
| `GUILD_ID`        | ID d'un serveur pour synchroniser les slash instantanément (dev) | global |
| `OWNER_ID`        | ID Discord de l'owner principal du bot                           | —      |
| `REPO_URL`        | Dépôt GitHub (liens de PR dans les notifications de mise à jour)  | Watcher|
| `SUPPORT_SERVER`  | Invitation du serveur de support (MP de blacklist `banserv`)      | —      |
| `OAUTH_*`, `WEB_*`| Panel web (voir plus bas)                                        | —      |

> Sans `GUILD_ID`, les commandes slash sont synchronisées globalement, ce qui
> peut prendre jusqu'à une heure la première fois.

## Commandes

> `help` présente les commandes **par catégories** (une page par catégorie,
> navigation par boutons ◀️/▶️) et précise la permission requise (🔒).
> `help <commande>` affiche le détail (description, usage, catégorie,
> permission, alias). Les listes ci-dessous sont un résumé ; la référence
> complète est générée dans [`docs/commands/`](docs/commands/README.md).

### Général & infos

| Commande | Description |
|----------|-------------|
| `help [commande]` | Aide générale ou détail d'une commande |
| `bonjour` | Le bot vous salue |
| `ping` | Latence du bot |
| `status` | Version, ping et nombre de serveurs |
| `uptime` | Depuis combien de temps le bot tourne |
| `botinfo` | Informations et statistiques du bot |
| `userinfo [membre]` | Infos détaillées d'un utilisateur |
| `avatar [membre]` | Avatar d'un utilisateur (liens PNG/JPG/WEBP/GIF) |
| `serverinfo` | Informations sur le serveur |
| `membercount` | Nombre de membres (humains / bots) |

### Utilitaire

| Commande | Description |
|----------|-------------|
| `remindme <message> <temps>` | Rappel en MP après un délai (ex: `1h30m`) |
| `poll <question [\| opt1 \| opt2…]>` | Sondage à réactions |
| `roll [NdM]` | Lance des dés (ex: `2d6`, `d20`) |
| `coinflip` | Pile ou face |
| `8ball <question>` | La boule magique répond |
| `choose <a \| b \| …>` | Choisit une option au hasard |
| `giveaway <durée> <gagnants> <prix>` | Lance un giveaway (réaction 🎉) — *admin* |
| `gend <id>` / `greroll <id>` | Fin anticipée / nouveau tirage — *admin* |

### Modération (permission **Administrateur** sauf mention contraire)

| Commande | Description |
|----------|-------------|
| `kick <membre> [raison]` | Expulse un membre (MP + raison) — *Expulser des membres* |
| `ban <membre\|id> [durée] [raison]` | Bannit (temporaire possible, ban par ID) — *Bannir des membres* |
| `unban <id>` | Débannit par ID — *Bannir des membres* |
| `mute <membre> <durée>` / `unmute <membre>` | Timeout Discord (max 28 j) |
| `mutemicro` / `unmutemicro <membre>` | Couper/rendre le micro en vocal — *Rendre muet* |
| `mutecasque` / `unmutecasque <membre>` | Couper/rendre le son en vocal — *Rendre sourd* |
| `move <membre> <salon>` | Déplace un membre en vocal — *Déplacer des membres* |
| `warn <membre>` / `unwarn` / `warns` | Avertissements (escalade, voir plus bas) |
| `confine <membre>` / `unconfine <membre>` | Isole un membre dans un salon dédié |
| `clear <nombre>` | Supprime des messages (max 100) — *Gérer les messages* |
| `userstatus <membre>` | Historique des sanctions + notes |
| `note <membre> <texte>` / `delnote <membre> <n°>` | Notes libres au dossier |
| `watch` / `unwatch` / `watchlist` | Surveille l'activité d'un membre |
| `logs <on\|off> <catégorie>` / `logs status` | Logs Discord par catégorie |
| `bienvenue …` | Messages de bienvenue/au revoir + MP (voir plus bas) |
| `ticket <salon> <message>` / `closeticket` | Système de tickets à bouton |
| `antibot` / `antiraid` / `antipub` / `antispam` / `antiinsulte` `<on/off>` | Automodération |
| `protections` | État de toutes les protections |
| `analyse` | Courbes d'activité du serveur sur 7 jours |
| `langue <fr/en>` | Langue du bot pour ce serveur |

### Propriétaire du serveur

| Commande | Description |
|----------|-------------|
| `prefixe [nouveau\|reset]` | Affiche/change le préfixe du bot sur ce serveur |
| `export <txt\|csv\|pdf> [période]` | Exporte le journal de modération |
| `contactowner <message>` | Envoie un MP aux owners du bot (infos serveur) |

### Owner du bot (préfixe uniquement)

Réservées aux **owners du bot** (l'owner principal `OWNER_ID`, plus les owners
additionnels). Fonctionnent partout, y compris en MP, indépendamment des
permissions du serveur.

| Commande | Description |
|----------|-------------|
| `addowner` / `rmowner` / `owners` | Gestion des owners (l'owner principal est protégé) |
| `helpowner` | Liste les commandes d'owner |
| `central` | Tableau de bord global du bot |
| `serveurs` | Détaille chaque serveur (une page par serveur) |
| `invite <id>` | Génère une invitation vers un serveur du bot |
| `respond <id\|all> <message>` | MP à un propriétaire de serveur (ou annonce) |
| `leave <id>` | Fait quitter un serveur au bot |
| `banserv <id>` / `unbanserv <id>` / `banservs` | Blacklist de serveurs |
| `reload [cog\|all]` / `shutdown` / `say <message>` | Contrôle du bot |

## Barème des avertissements

Chaque niveau attribue un rôle `Warn N` (sans permission) et applique une
sanction :

| Niveau | Sanction |
|--------|----------|
| 1 | Simple avertissement |
| 2 | Mute (timeout) 5 minutes |
| 3 | Mute (timeout) 1 heure |
| 4 | Confinement pendant une semaine |
| 5 | Bannissement permanent |

> Le compteur est persistant (`warns.json`). Les bans temporaires et le
> confinement du niveau 4 sont **persistés** (date de fin précise) et
> **repris automatiquement au démarrage** du bot.

## Automodération

Active en permanence, ignore les bots et les administrateurs.

- **Anti-bot / anti-raid / anti-pub / anti-spam / anti-insulte** : activables
  par commande (`<on/off>`).
- **Anti-majuscules** : message à plus de 75 % de majuscules (≥ 8 lettres)
  supprimé.
- **Anti-emojis** : message composé à plus de 75 % d'emojis (≥ 5) supprimé.

Escalation par utilisateur et par type : 1re infraction → avertissement, 2e →
avertissement officiel, 3e et + → mute progressif. Les compteurs
d'automodération sont en mémoire (réinitialisés au redémarrage).

## Bienvenue / au revoir

Groupe `bienvenue` (admin) : `salon` (salon des messages), `message` (arrivée),
`aurevoir` (départ), `mp <on/off>` (**MP de bienvenue**), `mpmessage` (message
du MP), `config` (état). Placeholders disponibles : `{user}`, `{name}`,
`{server}`, `{count}`.

## Tickets

`ticket <salon> <message>` poste un panneau avec un **bouton persistant**
(fonctionne après un redémarrage). Un clic crée un salon privé `ticket-<n°>`
visible du seul membre + admins ; `closeticket` retire l'accès du membre et
archive le salon (`closed-<n°>`).

## Panel web (administration)

Un panel web optionnel, avec **connexion Discord (OAuth2)**, affiche des
graphiques (serveurs, membres, utilisation par serveur).

- **Accès** : les **owners** voient toutes les données ; un **administrateur**
  voit les serveurs qu'il administre ; les autres sont refusés.
- **Dashboard owner** en trois pages — **Général** (analytics + contrôle),
  **Analytics** (par serveur ou agrégé) et **Live** (console en direct).
- **Activation** : renseignez `OAUTH_CLIENT_ID` et `OAUTH_CLIENT_SECRET` dans
  `.env` (sinon le panel ne démarre pas) ; ajoutez `OAUTH_REDIRECT_URI` dans
  les *Redirects* OAuth2 de l'application Discord. Écoute sur `WEB_HOST`
  (`127.0.0.1` par défaut) / `WEB_PORT`.
- Pages **publiques** : `/privacy` et `/terms` (pour les champs du portail
  Discord).

👉 Guide pas à pas : [`docs/OAUTH_SETUP.md`](docs/OAUTH_SETUP.md).

## Déploiement automatique

`scripts/deploy.sh` déploie chaque push GitHub : il récupère la branche suivie,
remplace le code local (`git reset --hard`, en **préservant** `data/`, `.env`,
`logs/`), réinstalle les dépendances si besoin, puis redémarre le bot —
via **systemd** si un service est configuré, sinon via
[`scripts/watcher-ctl.sh`](scripts/watcher-ctl.sh) (process Python autonome
avec relance auto). `scripts/install-autodeploy.sh` installe le lancement
périodique (timer systemd ou cron) en une commande.

👉 Guide complet : [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Owners du bot & notifications

Lorsqu'un owner du bot rejoint un serveur, celui-ci lui attribue
automatiquement un rôle `owner-claudebot` (sans permission ; nécessite **Gérer
les rôles**). Les owners sont prévenus en MP à chaque arrivée/départ de serveur
(`guildnotify`) et sur erreur inattendue (`errorreport`). L'owner principal
(`OWNER_ID`) ne peut pas être retiré ; les owners additionnels persistent dans
`owners.json`.

## Messages d'erreur

Un gestionnaire global affiche un message clair et traduit lorsqu'une commande
échoue (permissions manquantes précisées, etc.) sans jamais relayer une
exception brute.
