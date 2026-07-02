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
