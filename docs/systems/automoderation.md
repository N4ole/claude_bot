# Système d'automodération

Filtres de messages activables **par serveur**. Ils ignorent les bots et les
**administrateurs**. L'état de chaque filtre est visible via `§protections`.

## Filtres activables
| Commande | Effet |
|----------|-------|
| `§antipub <on/off>` | Supprime les messages contenant une **invitation Discord** |
| `§antispam <on/off>` | Au-delà de 5 messages en 5 s : suppression + mute (timeout) 1 min |
| `§antiinsulte <on/off>` | Supprime les messages contenant une **insulte** détectée |

## Filtres toujours actifs
- **Anti-majuscules** : message à plus de 75 % de majuscules (≥ 8 lettres).
- **Anti-emojis** : message composé à plus de 75 % d'emojis (≥ 5).

Escalation par utilisateur et par type : 1re infraction → avertissement,
2e → avertissement officiel, 3e et + → mute (timeout) 5, 10, 15… min.

## Détection des insultes
Voir [`badwords`](../../utils/badwords.py) : dictionnaire **multilingue**
(fr, en, es, it, de, pt, arabe translittéré) avec normalisation gérant les
orthographes alternatives (leet `c0nnard`, lettres répétées, espacées, accents,
ponctuation) et des garde-fous contre les faux positifs.

## Persistance
Réglages on/off dans `data/guild_settings.json`. Les compteurs anti-spam et
d'escalation sont en mémoire (réinitialisés au redémarrage).
