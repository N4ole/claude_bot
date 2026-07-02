# Déploiement automatique depuis GitHub

Ce guide explique comment faire en sorte que **tout push sur GitHub se
déploie sur le serveur** qui héberge Watcher, à l'aide du script
[`scripts/deploy.sh`](../scripts/deploy.sh).

Principe : le serveur exécute périodiquement `deploy.sh`, qui compare la
version locale à celle de GitHub. S'il y a du nouveau, il **remplace le code
local par celui de GitHub** (`git reset --hard`), réinstalle les dépendances
si `requirements.txt` a changé, puis redémarre le bot.

> Les fichiers **non suivis par git** (`data/*.json`, `logs/`, `.env`) ne
> sont **jamais** écrasés par le déploiement : la configuration et les
> données runtime sont préservées.

## 1. Prérequis

- Le dépôt est cloné sur le serveur et la branche de production est
  suivie (par défaut `main`).
- Python et `pip` sont installés (idéalement un virtualenv).
- Le bot tourne comme un **service systemd** (voir §2).

## 2. Service systemd (exemple)

Créez `/etc/systemd/system/watcher.service` :

```ini
[Unit]
Description=Watcher (bot Discord)
After=network-online.target

[Service]
Type=simple
User=watcher
WorkingDirectory=/opt/watcher
ExecStart=/opt/watcher/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activez-le :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now watcher
```

## 3. Déploiement manuel

```bash
cd /opt/watcher
DEPLOY_BRANCH=main DEPLOY_SERVICE=watcher scripts/deploy.sh
```

Variables disponibles :

| Variable         | Défaut     | Rôle                                        |
|------------------|------------|---------------------------------------------|
| `DEPLOY_BRANCH`  | `main`     | Branche GitHub à déployer                   |
| `DEPLOY_SERVICE` | `watcher`  | Service systemd à redémarrer                |
| `DEPLOY_PYTHON`  | `python3`  | Interpréteur utilisé pour `pip install`     |

## 4. Déploiement « à chaque push » (cron)

Pour déployer automatiquement, lancez `deploy.sh` toutes les minutes via
cron. Il ne redémarre le bot **que** s'il y a réellement de nouveaux commits.

```cron
# crontab -e  (utilisateur qui possède le dépôt)
* * * * * cd /opt/watcher && DEPLOY_BRANCH=main DEPLOY_SERVICE=watcher \
  scripts/deploy.sh >> /opt/watcher/logs/deploy.log 2>&1
```

Le redémarrage `systemctl` nécessite les droits : autorisez l'utilisateur du
bot à redémarrer **uniquement** ce service, via sudoers :

```sudoers
# /etc/sudoers.d/watcher-deploy
watcher ALL=(root) NOPASSWD: /usr/bin/systemctl restart watcher
```

### Alternative : timer systemd

À la place de cron, un timer systemd (`watcher-deploy.timer` +
`watcher-deploy.service` de type `oneshot` appelant `deploy.sh`) fait le même
travail avec une meilleure intégration aux logs (`journalctl`).

## 5. Variante : déploiement instantané par webhook

Le cron introduit un délai (jusqu'à 1 min). Pour un déploiement **immédiat**
au push, exposez un petit endpoint qui exécute `deploy.sh` à la réception
d'un webhook GitHub « push » (vérifiez la signature `X-Hub-Signature-256`
avec un secret partagé). Cette voie demande un port public et davantage de
durcissement ; le cron reste l'option la plus simple et sans surface réseau
supplémentaire.

## Notes de sécurité

- `git reset --hard` **écrase** toute modification locale suivie par git :
  ne modifiez jamais le code directement sur le serveur, faites-le via
  GitHub.
- Limitez le `NOPASSWD` sudo au **seul** `systemctl restart <service>`.
- Gardez `.env` (token, secrets) hors du dépôt : il est déjà `gitignored`
  et préservé par le déploiement.
