# Documentation ClaudeBot

La documentation est organisée sur trois axes.

## 📌 Par commande
Une fiche par commande (description, usage, catégorie, permission, alias).

➡️ [`commands/`](commands/README.md)

## 🗂️ Par catégorie
Une page par catégorie regroupant ses commandes.

➡️ [`categories/`](categories/README.md) — 🔧 Général · 📊 Infos · 🎲 Utilitaire ·
🛡️ Modération · 👑 Owner · 👑 Propriétaire de serveur

## 🧩 Par système
Documentation conceptuelle de chaque système (fonctionnement, persistance,
permissions requises).

➡️ [`systems/`](systems/README.md)

## Guides
- [Configurer l'OAuth2 pour le panel web](OAUTH_SETUP.md)

---

> Les fiches **par commande** et **par catégorie** sont générées automatiquement
> à partir des métadonnées du bot :
>
> ```bash
> python -m scripts.gen_docs
> ```
>
> Relancez cette commande après avoir ajouté ou modifié une commande pour
> garder la documentation à jour.
