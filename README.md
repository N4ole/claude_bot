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
    └── ping.py
```

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

> Sans `GUILD_ID`, les commandes slash sont synchronisées globalement, ce qui
> peut prendre jusqu'à une heure la première fois.

## Ajouter une commande

Créez un fichier `cogs/ma_commande.py` sur le modèle des cogs existants. Il sera
chargé automatiquement au démarrage.

## Commandes disponibles

| Commande   | Description                          |
|------------|--------------------------------------|
| `help`     | Liste les commandes disponibles      |
| `bonjour`  | Le bot vous salue                    |
| `ping`     | Affiche la latence du bot            |

### Commandes d'administration

Réservées aux membres possédant la permission **Administrateur**.

| Commande            | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `watch <membre>`    | Surveille un utilisateur : crée la catégorie `WATCHED USER` et un salon privé `<user>-watched` où sont recopiés ses messages (envoyés, modifiés, supprimés) et son activité vocale (connexion/déconnexion, heure de sortie et durée de présence). |
| `unwatch <membre>`  | Arrête la surveillance (le salon de log est conservé).          |
| `watchlist`         | Liste les utilisateurs surveillés sur le serveur.               |

> Le salon de log n'est visible que par les administrateurs et le bot.
> La surveillance persiste entre les redémarrages (`watched.json`).
>
> **Intents requis** (à activer dans le portail développeur Discord) :
> *MESSAGE CONTENT*, *SERVER MEMBERS* et *PRESENCE/VOICE* — le bot demande
> `members`, `voice_states` et `message_content`. Le bot doit aussi disposer
> de la permission **Gérer les salons**.
