# Système d'analytics (commande analyse)

## Commande
- `§analyse` — génère des **courbes** d'activité du serveur sur **7 jours**.

Réservée aux **administrateurs**.

## Métriques (3 courbes)
1. Nombre de **membres** par jour.
2. **Messages par membre et par jour** (messages ÷ membres).
3. **Arrivées / Départs** (deux courbes).

Le graphique est rendu en image PNG (matplotlib, backend `Agg`) et envoyé dans
un embed.

## Collecte
- [`utils/analytics.py`](../../utils/analytics.py) : stockage quotidien par
  serveur (`data/analytics.json`), purge au-delà de 60 jours.
- Le cog [`cogs/analyse.py`](../../cogs/analyse.py) accumule messages / arrivées
  / départs dans un **tampon en mémoire** flushé chaque minute (qui enregistre
  aussi le nombre de membres du jour), pour éviter d'écrire à chaque message.

> Les données s'accumulent à partir de l'activation ; les jours sans données
> affichent zéro.
