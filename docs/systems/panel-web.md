# Système du panel web

Panel d'administration optionnel avec **connexion Discord (OAuth2)**.

## Activation
Renseignez `OAUTH_CLIENT_ID` et `OAUTH_CLIENT_SECRET` dans le `.env` (sinon le
panel ne démarre pas). Guide complet : [`../OAUTH_SETUP.md`](../OAUTH_SETUP.md).

## Accès
- **Owners** du bot → toutes les données.
- **Administrateurs** d'un serveur où le bot est présent → données des serveurs
  qu'ils administrent.
- Autres → refusés.

## Contenu
- Graphiques : évolution du nombre de serveurs et du total de membres,
  évolution des membres par serveur, utilisation (commandes) par serveur.
- **Analytics** (owners) : cartes serveurs, membres, commandes, ping, uptime.
- **Contrôle du bot** (owners) : changer le statut, recharger les cogs.
- Interface au thème **néon**.

## Architecture
- [`web/web_app.py`](../../web/web_app.py) — application aiohttp (OAuth +
  routes `/`, `/login`, `/callback`, `/logout`, `/api/stats`, `/api/control/*`).
- [`web/stats.py`](../../web/stats.py) — séries temporelles (`data/stats.json`).
- [`cogs/webpanel.py`](../../cogs/webpanel.py) — démarre le serveur et
  échantillonne les statistiques (chaque heure + à chaque join/leave).
