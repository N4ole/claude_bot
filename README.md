# claude_bot

Bot Discord en Python supportant à la fois les **commandes préfixe** (`§`) et
les **commandes slash** (`/`), avec une architecture multi-fichiers (un fichier
par commande).

## Structure

```
claude_bot/
├── main.py          # Point d'entrée : lance le bot
├── bot.py           # Classe du bot + chargement automatique des cogs
├── config.py        # Configuration (token, préfixe, guild id)
├── requirements.txt
├── .env.example     # Modèle de configuration
└── cogs/            # Un fichier par commande
    ├── help.py
    ├── bonjour.py
    ├── ping.py
    ├── watch.py
    └── owner/        # Commandes réservées aux owners du bot
        ├── manage.py     # addowner / rmowner / owners
        ├── reload.py     # reload
        ├── shutdown.py   # shutdown
        └── say.py        # say
```

Les cogs sont chargés récursivement : ajouter un fichier dans `cogs/` **ou**
dans un sous-dossier (comme `cogs/owner/`) suffit pour ajouter une commande.

Mentionner le bot (`@ClaudeBot` seul) affiche un message de présentation.

Les **owners du bot** peuvent utiliser ses commandes en **message privé** avec
lui (les commandes nécessitant un serveur restent, elles, réservées aux
serveurs). En MP, les commandes des non-owners sont ignorées.

Chaque commande utilise `@commands.hybrid_command`, ce qui la rend disponible
**à la fois** en préfixe (`§ping`) et en slash (`/ping`) sans duplication.

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
```

Renseignez ensuite votre `DISCORD_TOKEN` dans le fichier `.env`.

Dans le portail développeur Discord, activez l'intent **MESSAGE CONTENT**
(nécessaire pour les commandes préfixe).

## Lancement

```bash
python main.py
```

## Configuration (`.env`)

| Variable         | Description                                                      | Défaut |
|------------------|------------------------------------------------------------------|--------|
| `DISCORD_TOKEN`  | Token du bot (obligatoire)                                        | —      |
| `COMMAND_PREFIX` | Préfixe des commandes texte                                       | `§`    |
| `GUILD_ID`       | ID d'un serveur pour synchroniser les slash instantanément (dev) | global |
| `OWNER_ID`       | ID Discord de l'owner principal du bot                           | —      |

> Sans `GUILD_ID`, les commandes slash sont synchronisées globalement, ce qui
> peut prendre jusqu'à une heure la première fois.

## Ajouter une commande

Créez un fichier `cogs/ma_commande.py` sur le modèle des cogs existants. Il sera
chargé automatiquement au démarrage.

## Commandes disponibles

| Commande   | Description                          |
|------------|--------------------------------------|
| `help`     | Liste les commandes disponibles (hors commandes d'owner) |
| `bonjour`  | Le bot vous salue                    |
| `ping`     | Affiche la latence du bot            |
| `userinfo [membre]` | Affiche les informations détaillées d'un utilisateur (défaut : soi-même) |
| `avatar [membre]`   | Affiche l'avatar d'un utilisateur (avec liens PNG/JPG/WEBP/GIF) |
| `uptime`   | Affiche depuis combien de temps le bot tourne |
| `status`   | Version, ping et nombre de serveurs |
| `contactowner <message>` | Réservée au **propriétaire du serveur** : envoie le message en MP à tous les owners du bot, avec les infos du serveur et une invitation. |

### Commandes d'administration

Réservées aux membres possédant la permission **Administrateur**.

| Commande            | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `watch <membre>`    | Surveille un utilisateur : crée la catégorie `WATCHED USER` et un salon privé `<user>-watched` où sont recopiés ses messages (envoyés, modifiés, supprimés), ses réactions (ajoutées/retirées), ses changements de pseudo et de statut, et son activité vocale (connexion/déconnexion, heure de sortie et durée de présence). |
| `unwatch <membre>`  | Arrête la surveillance (le salon de log est conservé).          |
| `watchlist`         | Liste les utilisateurs surveillés sur le serveur.               |
| `confine <membre>`  | Isole un utilisateur : crée la catégorie `confinement` et un salon `confin-<user>` où seuls lui et les admins accèdent, et retire son accès au reste du serveur. |
| `unconfine <membre>`| Libère l'utilisateur : restaure son accès et supprime le salon de confinement. |
| `mute <membre> <durée>` | Coupe la parole (timeout Discord) pour une durée (`30s`, `5m`, `2h`, `1d`, `1h30m` ; max 28 j). |
| `unmute <membre>`   | Rend la parole à un utilisateur mute.                           |
| `clear <nombre>`    | Supprime un nombre de messages du salon (max 100 ; permission *Gérer les messages*). |
| `warn <membre>`     | Avertit un utilisateur (sanction progressive, voir ci-dessous). |
| `unwarn <membre>`   | Retire un avertissement et lève les sanctions temporaires.      |
| `warns <membre>`    | Affiche le nombre d'avertissements d'un utilisateur.            |

#### Barème des avertissements

Chaque niveau attribue un rôle `Warn N` (sans permission) qui remplace le
précédent, et applique une sanction :

| Niveau | Sanction |
|--------|----------|
| 1 | Simple avertissement |
| 2 | Mute (timeout) 5 minutes |
| 3 | Mute (timeout) 1 heure |
| 4 | Confinement pendant une semaine |
| 5 | Bannissement permanent |

> Le compteur est persistant (`warns.json`). Le confinement du niveau 4 est
> temporisé jusqu'à une **date de fin précise**, persistée dans
> `confinements.json` : la libération est **automatiquement reprise au démarrage**
> du bot (libération immédiate si l'échéance est déjà passée).

### Automodération

Active en permanence, ignore les bots et les administrateurs.

- **Anti-majuscules** : un message contenant **plus de 75 %** de lettres
  majuscules (au moins 8 lettres) est supprimé.
- **Anti-emojis** : un message composé à **plus de 75 %** d'emojis (au moins 5)
  est supprimé.

Escalation par utilisateur et par type d'infraction :

| Infraction | Sanction |
|------------|----------|
| 1re | Suppression + message d'avertissement |
| 2e | Suppression + avertissement officiel |
| 3e et + | Suppression + mute (timeout) de 5, 10, 15... minutes |

> Les compteurs d'automodération sont conservés en mémoire (réinitialisés au
> redémarrage du bot).

> Le salon de log n'est visible que par les administrateurs et le bot.
> La surveillance persiste entre les redémarrages (`watched.json`).

### Commandes d'owner

Réservées aux **owners du bot** (l'owner principal `OWNER_ID` du `.env`, plus
les owners additionnels). Fonctionnent partout, indépendamment des permissions
du serveur.

| Commande            | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `addowner <user>`   | Ajoute un owner additionnel (stocké dans `owners.json`).        |
| `rmowner <user>`    | Retire un owner additionnel (l'owner principal est protégé).    |
| `owners`            | Liste tous les owners du bot.                                   |
| `reload [cog]`      | Recharge un cog à chaud (ou `all` pour tout recharger).         |
| `shutdown`          | Éteint le bot.                                                  |
| `say <message>`     | Fait parler le bot dans le salon courant.                      |
| `helpowner`         | Liste les commandes d'owner (**préfixe uniquement**).          |
| `serveurs`          | Liste les serveurs du bot, triés par nombre de membres (nom, ID, membres, ancienneté). |
| `invite <serverid>` | Génère une invitation vers un serveur où se trouve le bot.     |

Ces commandes sont regroupées dans le dossier `cogs/owner/`.

Par ailleurs, lorsqu'un owner du bot rejoint un serveur où le bot est présent,
celui-ci lui attribue automatiquement un rôle **`owner-claudebot`** (sans
aucune permission). Cela nécessite la permission **Gérer les rôles** pour le bot.

> L'owner principal est défini par `OWNER_ID` dans le `.env` et ne peut pas
> être retiré. Les owners additionnels persistent dans `owners.json`.
>
> **Intents requis** (à activer dans le portail développeur Discord) :
> *MESSAGE CONTENT*, *SERVER MEMBERS* et *PRESENCE INTENT* — le bot demande
> `members`, `voice_states`, `presences` et `message_content`. Le bot doit
> aussi disposer de la permission **Gérer les salons**.
