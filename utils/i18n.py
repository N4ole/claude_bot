"""Internationalisation (i18n) du bot : français (défaut) et anglais.

Utilisation :
    from utils.i18n import t
    await ctx.send(t(ctx, "ping.result", ms=42))

La langue est déterminée par le serveur (réglage `lang`, voir storage), ou
français par défaut. `t()` accepte un `Context`, un `guild` (ou son id), ou
None (→ français).
"""
from utils import storage

DEFAULT = "fr"
LANGS = ("fr", "en")

# Catalogue des chaînes : clé -> {lang: modèle}. Les modèles utilisent la
# syntaxe str.format (ex. "{ms}").
_CATALOG: dict[str, dict[str, str]] = {
    # --- Commande langue ---
    "lang.set": {
        "fr": "✅ Langue du serveur définie sur **Français**.",
        "en": "✅ Server language set to **English**.",
    },
    "lang.current": {
        "fr": "🌍 Langue actuelle : **Français**. Utilise `langue fr` ou "
              "`langue en`.",
        "en": "🌍 Current language: **English**. Use `langue fr` or `langue en`.",
    },
    "lang.invalid": {
        "fr": "❌ Langue invalide. Choix : `fr` (français) ou `en` (anglais).",
        "en": "❌ Invalid language. Choose: `fr` (French) or `en` (English).",
    },
    # --- Général ---
    "ping.result": {
        "fr": "🏓 Pong ! Latence : **{ms} ms**",
        "en": "🏓 Pong! Latency: **{ms} ms**",
    },
    "bonjour": {
        "fr": "👋 Bonjour {user} !",
        "en": "👋 Hello {user}!",
    },
    # --- Erreurs communes ---
    "error.missing_perms": {
        "fr": "⛔ Il te manque la permission suivante pour utiliser cette "
              "commande : **{perms}**.",
        "en": "⛔ You are missing the following permission to use this "
              "command: **{perms}**.",
    },
    "error.bot_missing_perms": {
        "fr": "⚠️ Il me manque la permission suivante pour exécuter cette "
              "commande : **{perms}**.",
        "en": "⚠️ I am missing the following permission to run this "
              "command: **{perms}**.",
    },
    "error.no_dm": {
        "fr": "❌ Cette commande s'utilise sur un serveur.",
        "en": "❌ This command can only be used in a server.",
    },
    "error.dm_only": {
        "fr": "❌ Cette commande s'utilise en message privé.",
        "en": "❌ This command can only be used in direct messages.",
    },
    "error.check_failure": {
        "fr": "⛔ Tu n'as pas la permission d'utiliser cette commande.",
        "en": "⛔ You don't have permission to use this command.",
    },
    "error.member_not_found": {
        "fr": "❌ Utilisateur introuvable.",
        "en": "❌ User not found.",
    },
    "error.bad_argument": {
        "fr": "❌ Argument invalide : {error}",
        "en": "❌ Invalid argument: {error}",
    },
    "error.missing_argument": {
        "fr": "❌ Argument manquant. Usage : `{usage}`",
        "en": "❌ Missing argument. Usage: `{usage}`",
    },
    "error.generic": {
        "fr": "❌ Une erreur est survenue lors de l'exécution.",
        "en": "❌ An error occurred while running the command.",
    },
    "error.owner_only": {
        "fr": "⛔ Cette commande est réservée aux owners du bot.",
        "en": "⛔ This command is restricted to the bot owners.",
    },
    # --- Mute ---
    "mute.bad_duration": {
        "fr": "❌ Durée invalide. Exemples : `30s`, `5m`, `2h`, `1d`, `1h30m`.",
        "en": "❌ Invalid duration. Examples: `30s`, `5m`, `2h`, `1d`, `1h30m`.",
    },
    "mute.too_long": {
        "fr": "❌ La durée maximale d'un mute est de 28 jours.",
        "en": "❌ The maximum mute duration is 28 days.",
    },
    "mute.forbidden": {
        "fr": "⛔ Impossible de mute ce membre (permissions ou hiérarchie).",
        "en": "⛔ Cannot mute this member (permissions or role hierarchy).",
    },
    "mute.failed": {
        "fr": "❌ Échec du mute : {error}",
        "en": "❌ Mute failed: {error}",
    },
    "mute.title": {"fr": "🔇 Mute", "en": "🔇 Mute"},
    "mute.done": {
        "fr": "{user} est mute.",
        "en": "{user} has been muted.",
    },
    "mute.until": {"fr": "Jusqu'à", "en": "Until"},
    "mute.relative": {"fr": "Soit", "en": "That is"},
    "unmute.not_muted": {
        "fr": "{user} n'est pas mute.",
        "en": "{user} is not muted.",
    },
    "unmute.failed": {
        "fr": "❌ Échec du unmute : {error}",
        "en": "❌ Unmute failed: {error}",
    },
    "unmute.done": {
        "fr": "🔊 {user} n'est plus mute.",
        "en": "🔊 {user} is no longer muted.",
    },
    # --- Clear ---
    "clear.bad_number": {
        "fr": "❌ Indique un nombre supérieur à 0.",
        "en": "❌ Provide a number greater than 0.",
    },
    "clear.done": {
        "fr": "🧹 {count} message(s) supprimé(s).",
        "en": "🧹 {count} message(s) deleted.",
    },
    # --- Remindme ---
    "remind.bad_duration": {
        "fr": "❌ Durée invalide. Exemples : `30s`, `5m`, `2h`, `1d`, `1h30m`.",
        "en": "❌ Invalid duration. Examples: `30s`, `5m`, `2h`, `1d`, `1h30m`.",
    },
    "remind.set": {
        "fr": "✅ Je te le rappellerai en MP dans **{duration}** ({when}).",
        "en": "✅ I'll remind you in DM in **{duration}** ({when}).",
    },
    "remind.fire": {
        "fr": "⏰ Rappel : {message}",
        "en": "⏰ Reminder: {message}",
    },
    # --- Toggle générique (anti*) ---
    "toggle.usage": {
        "fr": "❌ Utilise `{name} on` ou `{name} off`.",
        "en": "❌ Use `{name} on` or `{name} off`.",
    },
    # --- Automodération (escalation) ---
    "am.caps": {"fr": "Anti-majuscules", "en": "Anti-caps"},
    "am.emoji": {"fr": "Anti-emojis", "en": "Anti-emojis"},
    "am.warn1": {
        "fr": "{user} ⚠️ {label} : merci d'éviter. Ton message a été supprimé.",
        "en": "{user} ⚠️ {label}: please avoid this. Your message was deleted.",
    },
    "am.warn2": {
        "fr": "{user} ⚠️ Avertissement officiel ({label}).",
        "en": "{user} ⚠️ Official warning ({label}).",
    },
    "am.mute": {
        "fr": "{user} 🔇 Mute {minutes} min ({label}).",
        "en": "{user} 🔇 Muted {minutes} min ({label}).",
    },
    # --- Anti-bot ---
    "antibot.on": {
        "fr": "🤖 **Anti-bot activé** : les bots qui rejoignent seront "
              "automatiquement expulsés.",
        "en": "🤖 **Anti-bot enabled**: bots that join will be automatically "
              "kicked.",
    },
    "antibot.off": {
        "fr": "🤖 **Anti-bot désactivé**.",
        "en": "🤖 **Anti-bot disabled**.",
    },
    # --- Anti-raid ---
    "antiraid.on": {
        "fr": "🛡️ **Anti-raid activé** : les nouveaux membres devront valider "
              "un captcha dans #{channel} pour accéder au serveur.",
        "en": "🛡️ **Anti-raid enabled**: new members must solve a captcha in "
              "#{channel} to access the server.",
    },
    "antiraid.off": {
        "fr": "🛡️ **Anti-raid désactivé** : plus de captcha à l'arrivée.",
        "en": "🛡️ **Anti-raid disabled**: no more captcha on join.",
    },
    "antiraid.welcome": {
        "fr": "👋 Bienvenue {user} ! Pour accéder au serveur, recopie ce code : "
              "**`{code}`**\n(tu as {minutes} minutes et {attempts} essais).",
        "en": "👋 Welcome {user}! To access the server, type this code: "
              "**`{code}`**\n(you have {minutes} minutes and {attempts} tries).",
    },
    "antiraid.verified": {
        "fr": "✅ {user} vérifié, bienvenue !",
        "en": "✅ {user} verified, welcome!",
    },
    "antiraid.wrong": {
        "fr": "❌ {user} code incorrect, réessaie.",
        "en": "❌ {user} wrong code, try again.",
    },
    "antiraid.kicked": {
        "fr": "⛔ {user} n'a pas validé le captcha à temps.",
        "en": "⛔ {user} did not solve the captcha in time.",
    },
    # --- Anti-pub ---
    "antipub.on": {
        "fr": "🚫 **Anti-pub activé** : les invitations Discord seront "
              "supprimées.",
        "en": "🚫 **Anti-ad enabled**: Discord invites will be deleted.",
    },
    "antipub.off": {
        "fr": "🚫 **Anti-pub désactivé**.",
        "en": "🚫 **Anti-ad disabled**.",
    },
    "antipub.warn": {
        "fr": "🚫 {user} les invitations Discord sont interdites ici.",
        "en": "🚫 {user} Discord invites are not allowed here.",
    },
    # --- Anti-spam ---
    "antispam.on": {
        "fr": "⏱️ **Anti-spam activé** : au-delà de {max} messages en {window}s, "
              "l'utilisateur est mute {minutes} min.",
        "en": "⏱️ **Anti-spam enabled**: beyond {max} messages in {window}s, the "
              "user is muted for {minutes} min.",
    },
    "antispam.off": {
        "fr": "⏱️ **Anti-spam désactivé**.",
        "en": "⏱️ **Anti-spam disabled**.",
    },
    "antispam.warn": {
        "fr": "⏱️ {user} arrête de spammer — tu es mute {minutes} minute(s).",
        "en": "⏱️ {user} stop spamming — you are muted for {minutes} minute(s).",
    },
    # --- Anti-insulte ---
    "antiinsulte.on": {
        "fr": "🤬 **Anti-insulte activé** : les messages insultants seront "
              "supprimés.",
        "en": "🤬 **Anti-insult enabled**: insulting messages will be deleted.",
    },
    "antiinsulte.off": {
        "fr": "🤬 **Anti-insulte désactivé**.",
        "en": "🤬 **Anti-insult disabled**.",
    },
    "antiinsulte.warn": {
        "fr": "🤬 {user} les insultes ne sont pas tolérées ici.",
        "en": "🤬 {user} insults are not tolerated here.",
    },
    # --- Warn ---
    "warn.s1": {"fr": "simple avertissement", "en": "simple warning"},
    "warn.s2": {"fr": "mute (timeout) de 5 minutes", "en": "5-minute mute (timeout)"},
    "warn.s3": {"fr": "mute (timeout) d'une heure", "en": "1-hour mute (timeout)"},
    "warn.s4": {"fr": "confinement pendant une semaine",
                "en": "one-week confinement"},
    "warn.s5": {"fr": "bannissement permanent", "en": "permanent ban"},
    "warn.s5_fail": {"fr": "bannissement (échec — vérifiez les permissions)",
                     "en": "ban (failed — check permissions)"},
    "warn.title": {"fr": "⚠️ Avertissement", "en": "⚠️ Warning"},
    "warn.desc": {"fr": "{user} — **warn {level}/{max}**",
                  "en": "{user} — **warn {level}/{max}**"},
    "warn.field": {"fr": "Sanction", "en": "Sanction"},
    "unwarn.none": {"fr": "{user} n'a aucun avertissement.",
                    "en": "{user} has no warnings."},
    "unwarn.done": {"fr": "✅ {user} passe à **warn {level}/{max}**.",
                    "en": "✅ {user} is now at **warn {level}/{max}**."},
    "warns.count": {"fr": "{user} a **{count}/{max}** avertissement(s).",
                    "en": "{user} has **{count}/{max}** warning(s)."},
    # --- Confine ---
    "confine.already": {"fr": "⚠️ {user} est déjà confiné.",
                        "en": "⚠️ {user} is already confined."},
    "confine.done": {"fr": "🔒 {user} a été confiné dans {channel}.",
                     "en": "🔒 {user} has been confined in {channel}."},
    "confine.notice": {
        "fr": "🔒 {user} tu es confiné. Seuls les administrateurs peuvent te "
              "voir ici.",
        "en": "🔒 {user} you are confined. Only administrators can see you here.",
    },
    "unconfine.done": {"fr": "🔓 {user} a été libéré du confinement.",
                       "en": "🔓 {user} has been released from confinement."},
    # --- Watch ---
    "watch.already": {"fr": "⚠️ {user} est déjà surveillé.",
                      "en": "⚠️ {user} is already being watched."},
    "watch.done": {"fr": "👁️ Surveillance de {user} activée dans {channel}.",
                   "en": "👁️ Watching {user} enabled in {channel}."},
    "watch.topic": {"fr": "Surveillance de {user} (id: {id})",
                    "en": "Watching {user} (id: {id})"},
    "unwatch.not": {"fr": "⚠️ {user} n'est pas surveillé.",
                    "en": "⚠️ {user} is not being watched."},
    "unwatch.done": {
        "fr": "✅ Surveillance de {user} arrêtée. (Le salon de log n'est pas "
              "supprimé.)",
        "en": "✅ Stopped watching {user}. (The log channel is not deleted.)",
    },
    "watchlist.empty": {"fr": "Aucun utilisateur n'est surveillé sur ce serveur.",
                        "en": "No user is being watched on this server."},
    "watchlist.title": {"fr": "👁️ Utilisateurs surveillés",
                        "en": "👁️ Watched users"},
    "watch.deleted": {"fr": "#{id} (supprimé)", "en": "#{id} (deleted)"},
    # --- Watch : journal ---
    "watch.msg_sent": {"fr": "{user} — message envoyé",
                       "en": "{user} — message sent"},
    "watch.msg_edit": {"fr": "{user} — message modifié",
                       "en": "{user} — message edited"},
    "watch.msg_del": {"fr": "{user} — message supprimé",
                      "en": "{user} — message deleted"},
    "watch.no_text": {"fr": "*(aucun texte)*", "en": "*(no text)*"},
    "watch.channel": {"fr": "Salon", "en": "Channel"},
    "watch.link": {"fr": "Lien", "en": "Link"},
    "watch.goto": {"fr": "aller au message", "en": "go to message"},
    "watch.attachments": {"fr": "Pièces jointes", "en": "Attachments"},
    "watch.before": {"fr": "Avant", "en": "Before"},
    "watch.after": {"fr": "Après", "en": "After"},
    "watch.reaction_add": {"fr": "{user} — réaction ajoutée",
                           "en": "{user} — reaction added"},
    "watch.reaction_del": {"fr": "{user} — réaction retirée",
                           "en": "{user} — reaction removed"},
    "watch.reaction_added": {"fr": "Réaction ajoutée : {emoji}",
                             "en": "Reaction added: {emoji}"},
    "watch.reaction_removed": {"fr": "Réaction retirée : {emoji}",
                               "en": "Reaction removed: {emoji}"},
    "watch.message": {"fr": "Message", "en": "Message"},
    "watch.nick": {"fr": "{user} — pseudo modifié",
                   "en": "{user} — nickname changed"},
    "watch.none": {"fr": "*(aucun)*", "en": "*(none)*"},
    "watch.status": {"fr": "{user} — statut modifié",
                     "en": "{user} — status changed"},
    "watch.status_desc": {"fr": "Statut : **{before}** → **{after}**",
                          "en": "Status: **{before}** → **{after}**"},
    "watch.voice": {"fr": "{user} — vocal", "en": "{user} — voice"},
    "watch.voice_join": {"fr": "🔊 A rejoint **{channel}**",
                         "en": "🔊 Joined **{channel}**"},
    "watch.voice_leave": {"fr": "🔇 A quitté **{channel}**",
                          "en": "🔇 Left **{channel}**"},
    "watch.voice_move": {"fr": "↔️ Est passé de **{before}** à **{after}**",
                         "en": "↔️ Moved from **{before}** to **{after}**"},
    "watch.leave_time": {"fr": "Heure de sortie", "en": "Leave time"},
    "watch.duration": {"fr": "Durée de présence", "en": "Time spent"},
    # --- Protections ---
    "prot.title": {"fr": "🛡️ Protections du serveur",
                   "en": "🛡️ Server protections"},
    "prot.toggleable": {"fr": "Activables", "en": "Toggleable"},
    "prot.on": {"fr": "🟢 Activé", "en": "🟢 Enabled"},
    "prot.off": {"fr": "🔴 Désactivé", "en": "🔴 Disabled"},
    "prot.always": {"fr": "Toujours actives", "en": "Always on"},
    "prot.always_val": {
        "fr": "🔠 Anti-majuscules : **🟢**\n😀 Anti-emojis : **🟢**",
        "en": "🔠 Anti-caps: **🟢**\n😀 Anti-emojis: **🟢**",
    },
    "prot.footer": {
        "fr": "Active/désactive : antibot, antiraid, antipub, antispam <on/off>",
        "en": "Toggle: antibot, antiraid, antipub, antispam <on/off>",
    },
    "prot.antibot": {"fr": "🤖 Anti-bot", "en": "🤖 Anti-bot"},
    "prot.antiraid": {"fr": "🛡️ Anti-raid (captcha)", "en": "🛡️ Anti-raid (captcha)"},
    "prot.antipub": {"fr": "🚫 Anti-pub (invitations)",
                     "en": "🚫 Anti-ad (invites)"},
    "prot.antispam": {"fr": "⏱️ Anti-spam", "en": "⏱️ Anti-spam"},
    "prot.antiinsulte": {"fr": "🤬 Anti-insulte", "en": "🤬 Anti-insult"},
    # --- UserStatus ---
    "us.title": {"fr": "📋 Dossier de {user}", "en": "📋 Record of {user}"},
    "us.warns_label": {"fr": "⚠️ Avertissements", "en": "⚠️ Warnings"},
    "us.mute_label": {"fr": "🔇 Mutes", "en": "🔇 Mutes"},
    "us.unmute_label": {"fr": "🔊 Unmutes", "en": "🔊 Unmutes"},
    "us.confine_label": {"fr": "🔒 Confinements", "en": "🔒 Confinements"},
    "us.current": {"fr": "État actuel", "en": "Current status"},
    "us.warns_now": {"fr": "Avertissements actuels : **{count}/5**",
                     "en": "Current warnings: **{count}/5**"},
    "us.muted_until": {"fr": "🔇 Actuellement mute jusqu'à ",
                       "en": "🔇 Currently muted until "},
    "us.confined_now": {"fr": "🔒 Actuellement confiné",
                        "en": "🔒 Currently confined"},
    "us.total": {"fr": "Total", "en": "Total"},
    "us.no_sanction": {"fr": "Aucune sanction enregistrée.",
                       "en": "No sanction recorded."},
    "us.mute_time": {"fr": "⏱️ Temps de mute cumulé : **{duration}**",
                     "en": "⏱️ Total mute time: **{duration}**"},
    "us.recent": {"fr": "Dernières actions", "en": "Recent actions"},
    "us.by": {"fr": "par", "en": "by"},
    # --- Champs communs infos ---
    "f.id": {"fr": "ID", "en": "ID"},
    "f.owner": {"fr": "Propriétaire", "en": "Owner"},
    "f.created": {"fr": "Créé le", "en": "Created on"},
    "f.members": {"fr": "Membres", "en": "Members"},
    "f.channels": {"fr": "Salons", "en": "Channels"},
    "f.roles": {"fr": "Rôles", "en": "Roles"},
    "f.boosts": {"fr": "Boosts", "en": "Boosts"},
    "f.emojis": {"fr": "Émojis", "en": "Emojis"},
    "f.requested_by": {"fr": "Demandé par {user}", "en": "Requested by {user}"},
    # --- ServerInfo ---
    "si.members_val": {"fr": "{total} ({humans} 👤 / {bots} 🤖)",
                       "en": "{total} ({humans} 👤 / {bots} 🤖)"},
    "si.boosts_val": {"fr": "{count} (niveau {tier})",
                      "en": "{count} (level {tier})"},
    # --- BotInfo ---
    "bi.desc": {"fr": "Bot de modération et d'utilitaires.",
                "en": "Moderation and utility bot."},
    "bi.version": {"fr": "Version", "en": "Version"},
    "bi.servers": {"fr": "Serveurs", "en": "Servers"},
    "bi.ping": {"fr": "Ping", "en": "Ping"},
    "bi.uptime": {"fr": "Uptime", "en": "Uptime"},
    "bi.commands": {"fr": "Commandes", "en": "Commands"},
    "bi.prefix": {"fr": "Préfixe", "en": "Prefix"},
    # --- MemberCount ---
    "mc.title": {"fr": "👥 Membres", "en": "👥 Members"},
    "mc.desc": {
        "fr": "**{total}** au total\n👤 {humans} humains · 🤖 {bots} bots",
        "en": "**{total}** total\n👤 {humans} humans · 🤖 {bots} bots",
    },
    # --- Poll ---
    "poll.too_many": {"fr": "❌ 10 options maximum.",
                      "en": "❌ 10 options maximum."},
    "poll.title": {"fr": "📊 Sondage", "en": "📊 Poll"},
    "poll.by": {"fr": "Sondage lancé par {user}",
                "en": "Poll started by {user}"},
    # --- Roll ---
    "roll.bad": {"fr": "❌ Format invalide. Exemples : `d6`, `2d20`, `4d10`.",
                 "en": "❌ Invalid format. Examples: `d6`, `2d20`, `4d10`."},
    "roll.limits": {"fr": "❌ Entre 1 et 100 dés, de 2 à 1000 faces.",
                    "en": "❌ Between 1 and 100 dice, 2 to 1000 sides."},
    # --- Choose ---
    "choose.need": {"fr": "❌ Donne au moins deux options séparées par `|`.",
                    "en": "❌ Provide at least two options separated by `|`."},
    "choose.result": {"fr": "🤔 Je choisis : **{choice}**",
                      "en": "🤔 I choose: **{choice}**"},
    # --- UserInfo ---
    "ui.title": {"fr": "Informations sur {user}",
                 "en": "Information about {user}"},
    "ui.name": {"fr": "Nom", "en": "Name"},
    "ui.nick": {"fr": "Surnom", "en": "Nickname"},
    "ui.bot": {"fr": "Bot", "en": "Bot"},
    "ui.yes": {"fr": "Oui", "en": "Yes"},
    "ui.no": {"fr": "Non", "en": "No"},
    "ui.status": {"fr": "Statut", "en": "Status"},
    "ui.activity": {"fr": "Activité", "en": "Activity"},
    "ui.created": {"fr": "Compte créé", "en": "Account created"},
    "ui.joined": {"fr": "A rejoint le serveur", "en": "Joined the server"},
    "ui.boosting": {"fr": "Booste depuis", "en": "Boosting since"},
    "ui.roles": {"fr": "Rôles ({count})", "en": "Roles ({count})"},
    "ui.top_role": {"fr": "Rôle le plus haut", "en": "Top role"},
    "ui.none": {"fr": "*(aucun)*", "en": "*(none)*"},
    "status.online": {"fr": "🟢 En ligne", "en": "🟢 Online"},
    "status.idle": {"fr": "🌙 Absent", "en": "🌙 Idle"},
    "status.dnd": {"fr": "⛔ Ne pas déranger", "en": "⛔ Do not disturb"},
    "status.offline": {"fr": "⚫ Hors ligne", "en": "⚫ Offline"},
    # --- Avatar ---
    "avatar.title": {"fr": "Avatar de {user}", "en": "{user}'s avatar"},
    # --- Uptime ---
    "uptime.title": {"fr": "⏱️ Uptime", "en": "⏱️ Uptime"},
    "uptime.desc": {"fr": "Le bot tourne depuis **{duration}**.",
                    "en": "The bot has been running for **{duration}**."},
    "uptime.started": {"fr": "Démarré", "en": "Started"},
    # --- Status ---
    "st.title": {"fr": "📊 Statut du bot", "en": "📊 Bot status"},
    # --- ContactOwner ---
    "co.not_owner": {
        "fr": "⛔ Seul le propriétaire du serveur peut utiliser cette commande.",
        "en": "⛔ Only the server owner can use this command.",
    },
    "co.title": {"fr": "📨 Message d'un propriétaire de serveur",
                 "en": "📨 Message from a server owner"},
    "co.server": {"fr": "Serveur", "en": "Server"},
    "co.server_id": {"fr": "ID serveur", "en": "Server ID"},
    "co.owner": {"fr": "Propriétaire", "en": "Owner"},
    "co.invite": {"fr": "Invitation", "en": "Invite"},
    "co.no_invite": {"fr": "*(impossible de créer une invitation)*",
                     "en": "*(unable to create an invite)*"},
    "co.sent": {"fr": "✅ Ton message a été transmis à {count} owner(s) du bot.",
                "en": "✅ Your message was forwarded to {count} bot owner(s)."},
    "co.failed": {
        "fr": "❌ Impossible de contacter les owners du bot pour le moment.",
        "en": "❌ Unable to contact the bot owners at the moment.",
    },
    # --- respond (owner -> propriétaires de serveurs) ---
    "resp.dm_title": {"fr": "📬 Message des owners de Watcher",
                      "en": "📬 Message from the Watcher owners"},
    "resp.announce_title": {"fr": "📢 Annonce de Watcher",
                            "en": "📢 Watcher announcement"},
    "resp.from": {"fr": "Envoyé par", "en": "Sent by"},
    "resp.usage": {
        "fr": "Usage : `{prefix}respond <ID utilisateur | all> <message>`",
        "en": "Usage: `{prefix}respond <user ID | all> <message>`",
    },
    "resp.bad_id": {
        "fr": "❌ ID invalide. Indique un ID d'utilisateur (voir `{prefix}serveurs`) ou `all`.",
        "en": "❌ Invalid ID. Provide a user ID (see `{prefix}serveurs`) or `all`.",
    },
    "resp.sent_one": {
        "fr": "✅ Message envoyé à **{user}** (`{id}`).",
        "en": "✅ Message sent to **{user}** (`{id}`).",
    },
    "resp.fail_one": {
        "fr": "❌ Impossible d'envoyer un MP à `{id}` (introuvable ou MP fermés).",
        "en": "❌ Could not DM `{id}` (not found or DMs closed).",
    },
    "resp.no_owners": {
        "fr": "❌ Aucun propriétaire de serveur à contacter.",
        "en": "❌ No server owner to contact.",
    },
    "resp.announced": {
        "fr": "✅ Annonce envoyée à {sent} propriétaire(s) de serveur"
              " ({failed} échec(s)).",
        "en": "✅ Announcement sent to {sent} server owner(s)"
              " ({failed} failure(s)).",
    },
    # --- Mention (présentation) ---
    "mention.title": {"fr": "👋 Bonjour, je suis Watcher !",
                      "en": "👋 Hi, I'm Watcher!"},
    "mention.desc": {"fr": "Un bot de modération et d'utilitaires pour ton serveur.",
                     "en": "A moderation and utility bot for your server."},
    "mention.prefix": {"fr": "Préfixe", "en": "Prefix"},
    "mention.help": {"fr": "Aide", "en": "Help"},
    "mention.features": {"fr": "Fonctionnalités", "en": "Features"},
    "mention.features_val": {
        "fr": "• Modération (warn, mute, confine, clear...)\n"
              "• Automodération (anti-majuscules, anti-emojis)\n"
              "• Surveillance et infos utilisateurs",
        "en": "• Moderation (warn, mute, confine, clear...)\n"
              "• Automoderation (anti-caps, anti-emojis)\n"
              "• Watching and user info",
    },
    # --- Analyse ---
    "analyse.title": {"fr": "📈 Analyse du serveur (7 jours)",
                      "en": "📈 Server analysis (7 days)"},
    "analyse.chart_title": {"fr": "Analyse de {name} — 7 jours",
                            "en": "{name} analysis — 7 days"},
    "analyse.members": {"fr": "Nombre de membres", "en": "Member count"},
    "analyse.msg_per_member": {"fr": "Messages par membre et par jour",
                               "en": "Messages per member per day"},
    "analyse.joinleave": {"fr": "Arrivées / Départs", "en": "Joins / Leaves"},
    "analyse.joins": {"fr": "Arrivées", "en": "Joins"},
    "analyse.leaves": {"fr": "Départs", "en": "Leaves"},
    # --- CoinFlip ---
    "coin.heads": {"fr": "🪙 Pile", "en": "🪙 Heads"},
    "coin.tails": {"fr": "🪙 Face", "en": "🪙 Tails"},
    # --- Owner : manage ---
    "own.already": {"fr": "⚠️ {user} est déjà owner.",
                    "en": "⚠️ {user} is already an owner."},
    "own.added": {"fr": "✅ {user} est désormais owner du bot.",
                  "en": "✅ {user} is now a bot owner."},
    "own.principal_protect": {
        "fr": "⛔ L'owner principal ne peut pas être retiré.",
        "en": "⛔ The main owner cannot be removed.",
    },
    "own.removed": {"fr": "✅ {user} n'est plus owner du bot.",
                    "en": "✅ {user} is no longer a bot owner."},
    "own.not_owner": {"fr": "⚠️ {user} n'était pas owner.",
                      "en": "⚠️ {user} was not an owner."},
    "own.list_title": {"fr": "👑 Owners du bot", "en": "👑 Bot owners"},
    "own.list_empty": {"fr": "Aucun owner défini.", "en": "No owner set."},
    "own.principal": {"fr": "(principal)", "en": "(main)"},
    # --- Owner : say ---
    "say.sent": {"fr": "✅ Message envoyé.", "en": "✅ Message sent."},
    "say.missing": {"fr": "❌ Précisez le message à envoyer.",
                    "en": "❌ Please provide the message to send."},
    # --- Owner : shutdown ---
    "shutdown.msg": {"fr": "🛑 Extinction du bot...", "en": "🛑 Shutting down..."},
    # --- Owner : reload ---
    "reload.not_found": {"fr": "❌ Cog introuvable : `{cog}`",
                         "en": "❌ Cog not found: `{cog}`"},
    "reload.one": {"fr": "✅ Cog rechargé : `{cog}`",
                   "en": "✅ Cog reloaded: `{cog}`"},
    "reload.one_fail": {"fr": "❌ Échec du rechargement de `{cog}` : {error}",
                        "en": "❌ Failed to reload `{cog}`: {error}"},
    "reload.all_ok": {"fr": "✅ Rechargés : {count}",
                      "en": "✅ Reloaded: {count}"},
    "reload.all_fail": {"fr": "\n❌ Échecs :\n{failed}",
                        "en": "\n❌ Failures:\n{failed}"},
    # --- Owner : invite ---
    "invite.bad_id": {"fr": "❌ ID de serveur invalide.",
                      "en": "❌ Invalid server ID."},
    "invite.not_present": {"fr": "❌ Le bot n'est pas présent sur ce serveur.",
                           "en": "❌ The bot is not on that server."},
    "invite.no_channel": {
        "fr": "❌ Aucun salon ne permet au bot de créer une invitation sur "
              "**{name}**.",
        "en": "❌ No channel allows the bot to create an invite on **{name}**.",
    },
    "invite.failed": {"fr": "❌ Impossible de créer l'invitation : {error}",
                      "en": "❌ Unable to create the invite: {error}"},
    "invite.done": {"fr": "🔗 Invitation vers **{name}** : {url}",
                    "en": "🔗 Invite to **{name}**: {url}"},
    # --- Owner : servers ---
    "srv.none": {"fr": "Le bot n'est sur aucun serveur.",
                 "en": "The bot is on no server."},
    # --- HelpOwner ---
    "ho.not_found": {"fr": "❌ Commande owner introuvable : `{cmd}`",
                     "en": "❌ Owner command not found: `{cmd}`"},
    "ho.title": {"fr": "👑 Commandes d'owner", "en": "👑 Owner commands"},
    "ho.desc": {
        "fr": "Préfixe : `{prefix}` — commandes réservées aux owners du bot.\n"
              "Détail d'une commande : `{prefix}helpowner <commande>`.",
        "en": "Prefix: `{prefix}` — commands restricted to bot owners.\n"
              "Command details: `{prefix}helpowner <command>`.",
    },
    "ho.footer": {"fr": "{count} commande(s) d'owner",
                  "en": "{count} owner command(s)"},
    "ho.avail": {"fr": "Disponible en", "en": "Available in"},
    "ho.avail_both": {"fr": "préfixe `{prefix}` et slash `/`",
                      "en": "prefix `{prefix}` and slash `/`"},
    "ho.avail_prefix": {"fr": "préfixe uniquement", "en": "prefix only"},
    "ho.dm": {"fr": "En message privé", "en": "In direct messages"},
    "ho.dm_val": {"fr": "✅ oui (réservé aux owners)",
                  "en": "✅ yes (owners only)"},
    "ho.usage": {"fr": "Usage", "en": "Usage"},
    "ho.alias": {"fr": "Alias", "en": "Aliases"},
    "ho.legend": {
        "fr": "⟨ ⟩ = obligatoire · [ ] = facultatif · réservé aux owners",
        "en": "⟨ ⟩ = required · [ ] = optional · owners only",
    },
    # --- Central ---
    "central.title": {"fr": "🛰️ Centralisation Watcher",
                      "en": "🛰️ Watcher central dashboard"},
    "central.servers": {"fr": "🌐 Serveurs", "en": "🌐 Servers"},
    "central.servers_val": {
        "fr": "**{guilds}** serveurs\n**{members}** membres\n👤 {humans} · 🤖 {bots}",
        "en": "**{guilds}** servers\n**{members}** members\n👤 {humans} · 🤖 {bots}",
    },
    "central.mod": {"fr": "🛡️ Modération active", "en": "🛡️ Active moderation"},
    "central.mod_val": {
        "fr": "🔇 {muted} mute(s)\n🔒 {confined} confiné(s)\n👁️ {watched} surveillé(s)",
        "en": "🔇 {muted} mute(s)\n🔒 {confined} confined\n👁️ {watched} watched",
    },
    "central.warns": {"fr": "⚠️ Avertissements", "en": "⚠️ Warnings"},
    "central.warns_val": {
        "fr": "{users} utilisateur(s)\n{points} point(s) au total\n"
              "⏳ {timed} confinement(s) temporisé(s)",
        "en": "{users} user(s)\n{points} point(s) total\n"
              "⏳ {timed} timed confinement(s)",
    },
    "central.prot": {"fr": "🚨 Protections activées", "en": "🚨 Enabled protections"},
    "central.prot_line": {"fr": "{label} : **{count}** serveur(s)",
                          "en": "{label}: **{count}** server(s)"},
    "central.reminders": {"fr": "⏰ Rappels en attente", "en": "⏰ Pending reminders"},
    "central.owners": {"fr": "👑 Owners", "en": "👑 Owners"},
    "central.bot": {"fr": "⚙️ Bot", "en": "⚙️ Bot"},
    "central.bot_val": {"fr": "v{version} · {ping} ms\nUptime : {uptime}",
                        "en": "v{version} · {ping} ms\nUptime: {uptime}"},
    # --- Help ---
    "help.title": {"fr": "📖 Aide — {category}", "en": "📖 Help — {category}"},
    "help.desc": {
        "fr": "Préfixe `{prefix}` · aussi en slash `/` · 🔒 = permission requise.",
        "en": "Prefix `{prefix}` · also slash `/` · 🔒 = permission required.",
    },
    "help.page": {"fr": "Page {n}/{total} · {count} commande(s) au total",
                  "en": "Page {n}/{total} · {count} command(s) total"},
    "help.not_for_you": {"fr": "Ce menu n'est pas pour toi.",
                         "en": "This menu is not for you."},
    "help.not_found": {"fr": "❌ Commande introuvable : `{cmd}`",
                       "en": "❌ Command not found: `{cmd}`"},
    "help.no_cmd": {"fr": "Aucune commande disponible.",
                    "en": "No command available."},
    "help.cmd_title": {"fr": "Commande : {prefix}{name}",
                       "en": "Command: {prefix}{name}"},
    "help.no_desc": {"fr": "Pas de description.", "en": "No description."},
    "help.usage": {"fr": "Usage", "en": "Usage"},
    "help.category": {"fr": "Catégorie", "en": "Category"},
    "help.permission": {"fr": "Permission", "en": "Permission"},
    "help.perm_none": {"fr": "Aucune", "en": "None"},
    "help.avail": {"fr": "Disponible en", "en": "Available in"},
    "help.avail_both": {"fr": "préfixe `{prefix}` et slash `/`",
                        "en": "prefix `{prefix}` and slash `/`"},
    "help.avail_prefix": {"fr": "préfixe uniquement", "en": "prefix only"},
    "help.alias": {"fr": "Alias", "en": "Aliases"},
    "help.legend": {
        "fr": "⟨ ⟩ = obligatoire · [ ] = facultatif · {prefix}help pour la liste "
              "complète",
        "en": "⟨ ⟩ = required · [ ] = optional · {prefix}help for the full list",
    },
    # Catégories du help (pour rester traduites).
    "cat.general": {"fr": "🔧 Général", "en": "🔧 General"},
    "cat.info": {"fr": "📊 Infos", "en": "📊 Info"},
    "cat.util": {"fr": "🎲 Utilitaire", "en": "🎲 Utility"},
    "cat.mod": {"fr": "🛡️ Modération", "en": "🛡️ Moderation"},
    "cat.owner_server": {"fr": "👑 Propriétaire de serveur",
                         "en": "👑 Server owner"},
    "perm.admin": {"fr": "Administrateur", "en": "Administrator"},
    "perm.manage_messages": {"fr": "Gérer les messages", "en": "Manage Messages"},
    "perm.server_owner": {"fr": "Propriétaire du serveur", "en": "Server owner"},
    "perm.kick": {"fr": "Expulser des membres", "en": "Kick Members"},
    "perm.ban": {"fr": "Bannir des membres", "en": "Ban Members"},
    # Descriptions traduites des commandes (utilisées par le help).
    "cmddesc.kick": {"fr": "Expulse un utilisateur du serveur (avec raison).",
                     "en": "Kick a user from the server (with reason)."},
    "cmddesc.ban": {
        "fr": "Bannit un utilisateur (raison et durée optionnelle).",
        "en": "Ban a user (reason and optional duration)."},
    "cmddesc.unban": {"fr": "Débannit un utilisateur par son ID.",
                      "en": "Unban a user by their ID."},
    "cmddesc.8ball": {"fr": "Pose une question à la boule magique.",
                      "en": "Ask the magic 8-ball a question."},
    "cmddesc.analyse": {"fr": "Graphique d'activité du serveur sur 7 jours.",
                        "en": "7-day server activity chart."},
    "cmddesc.antibot": {"fr": "Active/désactive le blocage des bots (on/off).",
                        "en": "Enable/disable bot blocking (on/off)."},
    "cmddesc.antiinsulte": {
        "fr": "Active/désactive la suppression des insultes (on/off).",
        "en": "Enable/disable insult removal (on/off)."},
    "cmddesc.antipub": {
        "fr": "Active/désactive la suppression des invitations Discord (on/off).",
        "en": "Enable/disable Discord invite removal (on/off)."},
    "cmddesc.antiraid": {
        "fr": "Active/désactive le captcha à l'arrivée (on/off).",
        "en": "Enable/disable join captcha (on/off)."},
    "cmddesc.antispam": {"fr": "Active/désactive l'anti-spam (on/off).",
                         "en": "Enable/disable anti-spam (on/off)."},
    "cmddesc.avatar": {"fr": "Affiche l'avatar d'un utilisateur.",
                       "en": "Show a user's avatar."},
    "cmddesc.bonjour": {"fr": "Le bot vous dit bonjour.",
                        "en": "The bot says hello."},
    "cmddesc.botinfo": {"fr": "Affiche des informations sur le bot.",
                        "en": "Show information about the bot."},
    "cmddesc.choose": {
        "fr": "Choisit une option parmi plusieurs (séparées par « | »).",
        "en": "Pick one option among several (separated by “|”)."},
    "cmddesc.clear": {
        "fr": "Supprime un nombre de messages du salon (max 100).",
        "en": "Delete a number of messages from the channel (max 100)."},
    "cmddesc.coinflip": {"fr": "Lance une pièce : pile ou face.",
                         "en": "Flip a coin: heads or tails."},
    "cmddesc.confine": {"fr": "Isole un utilisateur dans un salon de confinement.",
                        "en": "Isolate a user in a confinement channel."},
    "cmddesc.contactowner": {
        "fr": "Contacte les owners du bot (réservé au propriétaire du serveur).",
        "en": "Contact the bot owners (server owner only)."},
    "cmddesc.help": {
        "fr": "Aide générale, ou détail d'une commande : help [commande].",
        "en": "General help, or details of a command: help [command]."},
    "cmddesc.langue": {"fr": "Choisit la langue du bot pour ce serveur (fr/en).",
                       "en": "Set the bot language for this server (fr/en)."},
    "cmddesc.membercount": {"fr": "Affiche le nombre de membres du serveur.",
                            "en": "Show the server member count."},
    "cmddesc.mute": {
        "fr": "Coupe la parole à un utilisateur pour une durée (ex: 5m, 1h30m).",
        "en": "Mute a user for a duration (e.g. 5m, 1h30m)."},
    "cmddesc.ping": {"fr": "Affiche la latence du bot.",
                     "en": "Show the bot latency."},
    "cmddesc.poll": {
        "fr": "Crée un sondage. Options séparées par des « | » (facultatif).",
        "en": "Create a poll. Options separated by “|” (optional)."},
    "cmddesc.protections": {"fr": "Affiche l'état des protections du serveur.",
                            "en": "Show the server protection status."},
    "cmddesc.remindme": {
        "fr": "Te rappelle un message en MP après un délai (ex: 1h30m).",
        "en": "Remind you of a message via DM after a delay (e.g. 1h30m)."},
    "cmddesc.roll": {"fr": "Lance des dés au format NdM (ex: 2d6, d20).",
                     "en": "Roll dice in NdM format (e.g. 2d6, d20)."},
    "cmddesc.serverinfo": {"fr": "Affiche les informations du serveur.",
                           "en": "Show server information."},
    "cmddesc.status": {"fr": "Version, ping et nombre de serveurs.",
                       "en": "Version, ping and server count."},
    "cmddesc.unconfine": {"fr": "Libère un utilisateur du confinement.",
                          "en": "Release a user from confinement."},
    "cmddesc.unmute": {"fr": "Rend la parole à un utilisateur mute.",
                       "en": "Unmute a muted user."},
    "cmddesc.unwarn": {"fr": "Retire un avertissement à un utilisateur.",
                       "en": "Remove a warning from a user."},
    "cmddesc.unwatch": {"fr": "Arrête la surveillance d'un utilisateur.",
                        "en": "Stop watching a user."},
    "cmddesc.uptime": {"fr": "Affiche depuis combien de temps le bot tourne.",
                       "en": "Show how long the bot has been running."},
    "cmddesc.userinfo": {"fr": "Affiche les informations d'un utilisateur.",
                         "en": "Show information about a user."},
    "cmddesc.userstatus": {"fr": "Affiche l'historique des sanctions d'un utilisateur.",
                           "en": "Show a user's punishment history."},
    "cmddesc.warn": {"fr": "Avertit un utilisateur (sanction progressive).",
                     "en": "Warn a user (escalating punishment)."},
    "cmddesc.warns": {"fr": "Affiche le nombre d'avertissements d'un utilisateur.",
                      "en": "Show a user's warning count."},
    "cmddesc.watch": {"fr": "Surveille un utilisateur et journalise son activité.",
                      "en": "Watch a user and log their activity."},
    "cmddesc.watchlist": {"fr": "Liste les utilisateurs actuellement surveillés.",
                          "en": "List currently watched users."},
    "cmddesc.logs": {
        "fr": "Active/désactive les logs Discord par type (on/off <type>).",
        "en": "Enable/disable Discord logs by type (on/off <type>)."},
    # --- Logs Discord ---
    "logs.usage": {
        "fr": "Usage : `{prefix}logs <on|off> <type>`\nTypes : {types}.",
        "en": "Usage: `{prefix}logs <on|off> <type>`\nTypes: {types}."},
    "logs.bad_type": {
        "fr": "❌ Type inconnu. Types disponibles : {types}.",
        "en": "❌ Unknown type. Available types: {types}."},
    "logs.on": {
        "fr": "✅ Logs **{type}** activés dans {channel}.",
        "en": "✅ **{type}** logs enabled in {channel}."},
    "logs.on_all": {
        "fr": "✅ Tous les types de logs ont été activés (catégorie **logs**).",
        "en": "✅ All log types have been enabled (**logs** category)."},
    "logs.off": {"fr": "✅ Logs **{type}** désactivés.",
                 "en": "✅ **{type}** logs disabled."},
    "logs.off_all": {"fr": "✅ Tous les logs ont été désactivés.",
                     "en": "✅ All logs have been disabled."},
    "logs.already_off": {"fr": "ℹ️ Les logs **{type}** ne sont pas activés.",
                         "en": "ℹ️ **{type}** logs are not enabled."},
    "logs.entry_cmd": {"fr": "📋 Commande `{prefix}{cmd}`",
                       "en": "📋 Command `{prefix}{cmd}`"},
    "logs.entry_error": {"fr": "⚠️ Échec `{prefix}{cmd}`",
                         "en": "⚠️ Failed `{prefix}{cmd}`"},
    "logs.f_user": {"fr": "Utilisateur", "en": "User"},
    "logs.f_channel": {"fr": "Salon", "en": "Channel"},
    "logs.f_via": {"fr": "Via", "en": "Via"},
    "logs.f_args": {"fr": "Arguments", "en": "Arguments"},
    "logs.f_error": {"fr": "Erreur", "en": "Error"},
    # --- Kick / Ban ---
    "mod.no_reason": {"fr": "Aucune raison fournie.", "en": "No reason provided."},
    "mod.reason_label": {"fr": "Raison", "en": "Reason"},
    "mod.duration_label": {"fr": "Durée", "en": "Duration"},
    "mod.permanent": {"fr": "Définitif", "en": "Permanent"},
    "kick.dm_title": {"fr": "👢 Tu as été expulsé", "en": "👢 You have been kicked"},
    "kick.dm_desc": {
        "fr": "Tu as été expulsé du serveur **{server}**.",
        "en": "You have been kicked from **{server}**."},
    "ban.dm_title": {"fr": "🔨 Tu as été banni", "en": "🔨 You have been banned"},
    "ban.dm_perm": {
        "fr": "Tu as été banni **définitivement** du serveur **{server}**.",
        "en": "You have been **permanently** banned from **{server}**."},
    "ban.dm_temp": {
        "fr": "Tu as été banni du serveur **{server}**.",
        "en": "You have been banned from **{server}**."},
    "ban.unban_dm_title": {
        "fr": "✅ Ton bannissement est terminé",
        "en": "✅ Your ban has ended"},
    "ban.unban_dm_desc": {
        "fr": "Ton bannissement du serveur **{server}** est terminé. Tu peux "
              "revenir avec cette invitation :",
        "en": "Your ban from **{server}** has ended. You can rejoin using "
              "this invite:"},
    "ban.unban_dm_no_invite": {
        "fr": "Ton bannissement du serveur **{server}** est terminé, mais je "
              "n'ai pas pu générer d'invitation.",
        "en": "Your ban from **{server}** has ended, but I couldn't generate "
              "an invite."},
    "kick.done": {
        "fr": "👢 **{user}** a été expulsé.\n**Raison :** {reason}",
        "en": "👢 **{user}** has been kicked.\n**Reason:** {reason}"},
    "kick.self": {"fr": "❌ Tu ne peux pas t'expulser toi-même.",
                  "en": "❌ You can't kick yourself."},
    "kick.hierarchy": {
        "fr": "❌ Tu ne peux pas expulser un membre dont le rôle est égal ou "
              "supérieur au tien.",
        "en": "❌ You can't kick a member whose role is equal to or higher "
              "than yours."},
    "kick.forbidden": {
        "fr": "❌ Je n'ai pas la permission d'expulser cet utilisateur "
              "(rôle trop haut ?).",
        "en": "❌ I don't have permission to kick this user (role too high?)."},
    "kick.failed": {"fr": "❌ Échec de l'expulsion : {error}",
                    "en": "❌ Kick failed: {error}"},
    "ban.title": {"fr": "🔨 Bannissement", "en": "🔨 Ban"},
    "ban.perm_desc": {
        "fr": "**{user}** a été banni **définitivement**.\n**Raison :** {reason}",
        "en": "**{user}** has been banned **permanently**.\n"
              "**Reason:** {reason}"},
    "ban.temp_desc": {
        "fr": "**{user}** a été banni.\n**Raison :** {reason}",
        "en": "**{user}** has been banned.\n**Reason:** {reason}"},
    "ban.until": {"fr": "Déban le", "en": "Unban on"},
    "ban.relative": {"fr": "Dans", "en": "In"},
    "ban.self": {"fr": "❌ Tu ne peux pas te bannir toi-même.",
                 "en": "❌ You can't ban yourself."},
    "ban.hierarchy": {
        "fr": "❌ Tu ne peux pas bannir un membre dont le rôle est égal ou "
              "supérieur au tien.",
        "en": "❌ You can't ban a member whose role is equal to or higher "
              "than yours."},
    "ban.forbidden": {
        "fr": "❌ Je n'ai pas la permission de bannir cet utilisateur "
              "(rôle trop haut ?).",
        "en": "❌ I don't have permission to ban this user (role too high?)."},
    "ban.failed": {"fr": "❌ Échec du bannissement : {error}",
                   "en": "❌ Ban failed: {error}"},
    "unban.bad_id": {
        "fr": "❌ Indique l'ID de l'utilisateur à débannir (ex: `123456789`).",
        "en": "❌ Provide the ID of the user to unban (e.g. `123456789`)."},
    "unban.not_banned": {
        "fr": "ℹ️ Aucun bannissement trouvé pour l'ID `{id}`.",
        "en": "ℹ️ No ban found for ID `{id}`."},
    "unban.done": {"fr": "✅ Utilisateur `{id}` débanni.",
                   "en": "✅ User `{id}` unbanned."},
    # --- Servers (détail owner) ---
    "srv.title": {"fr": "🌐 Serveurs du bot ({count})",
                  "en": "🌐 Bot servers ({count})"},
    "srv.members_val": {"fr": "**{count}**\n👤 {humans} · 🤖 {bots}",
                        "en": "**{count}**\n👤 {humans} · 🤖 {bots}"},
    "srv.channels": {"fr": "Salons", "en": "Channels"},
    "srv.roles_emojis": {"fr": "Rôles / Émojis / Stickers",
                         "en": "Roles / Emojis / Stickers"},
    "srv.roles_val": {
        "fr": "{roles} rôles\n{emojis}/{emoji_lim} émojis\n"
              "{stickers}/{sticker_lim} stickers",
        "en": "{roles} roles\n{emojis}/{emoji_lim} emojis\n"
              "{stickers}/{sticker_lim} stickers",
    },
    "srv.verif": {"fr": "Vérification", "en": "Verification"},
    "srv.bot_since": {"fr": "Bot présent depuis", "en": "Bot present since"},
    "srv.misc": {"fr": "Divers", "en": "Misc"},
    "srv.sys_channel": {"fr": "Salon système : {channel}",
                        "en": "System channel: {channel}"},
    "srv.afk": {"fr": "AFK : {channel} ({minutes} min)",
                "en": "AFK: {channel} ({minutes} min)"},
    "srv.locale": {"fr": "Langue : {locale}", "en": "Locale: {locale}"},
    "srv.vanity": {"fr": "Vanity : `/{code}`", "en": "Vanity: `/{code}`"},
    "srv.features": {"fr": "Fonctionnalités", "en": "Features"},
    "srv.footer": {"fr": "Serveur {index}/{total} · trié par nombre de membres",
                   "en": "Server {index}/{total} · sorted by member count"},
    "verif.none": {"fr": "Aucune", "en": "None"},
    "verif.low": {"fr": "Basse", "en": "Low"},
    "verif.medium": {"fr": "Moyenne", "en": "Medium"},
    "verif.high": {"fr": "Haute", "en": "High"},
    "verif.highest": {"fr": "Très haute", "en": "Highest"},
}

# Listes de réponses (sélectionnées par langue).
EIGHTBALL = {
    "fr": [
        "Oui, c'est certain.", "Sans aucun doute.", "Oui, absolument.",
        "C'est probable.", "Les signes disent oui.", "Peut-être.",
        "Difficile à dire, réessaie.",
        "Je ne peux pas prédire ça maintenant.",
        "Ne compte pas dessus.", "Ma réponse est non.", "Très douteux.",
        "C'est non.",
    ],
    "en": [
        "Yes, definitely.", "Without a doubt.", "Yes, absolutely.",
        "It is likely.", "Signs point to yes.", "Maybe.",
        "Hard to say, try again.", "I can't predict that right now.",
        "Don't count on it.", "My answer is no.", "Very doubtful.",
        "It's a no.",
    ],
}


def _resolve_lang(source) -> str:
    """Détermine la langue depuis un Context / guild / id / None."""
    guild_id = None
    if source is None:
        return DEFAULT
    guild = getattr(source, "guild", source)
    guild_id = getattr(guild, "id", guild)
    if not isinstance(guild_id, int):
        return DEFAULT
    lang = storage.get_setting(guild_id, "lang", DEFAULT)
    return lang if lang in LANGS else DEFAULT


def t(source, key: str, **kwargs) -> str:
    """Traduit `key` selon la langue de `source`, avec formatage `kwargs`."""
    entry = _CATALOG.get(key)
    if entry is None:
        return key
    lang = _resolve_lang(source)
    template = entry.get(lang) or entry.get(DEFAULT) or key
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template


def get_lang(source) -> str:
    """Renvoie la langue résolue ('fr' ou 'en')."""
    return _resolve_lang(source)
