"""Détection d'insultes multilingue avec orthographes alternatives.

Normalisation :
  - casse et accents (é -> e, ñ -> n) ;
  - « leet speak » (c0nnard, s@lope, pu7ain, b1tch...) ;
  - lettres répétées (connnnard -> conard) ;
  - ponctuation / séparateurs (c-o-n-n-a-r-d, con.nard) ;
  - lettres espacées (c o n n a r d).

Deux niveaux de détection :
  - `_WORDS` : correspondance en **mot entier** (+ pluriel). Réservé aux termes
    courts ou susceptibles d'apparaître dans des mots normaux (pute, con, ass,
    cul, cock...) pour éviter les faux positifs.
  - `_ROOTS` : correspondance en **sous-chaîne d'un mot** (attrape les dérivés :
    fucking, enculé, bitches...). Réservé à des racines longues et peu
    ambiguës.
  - `_PHRASES` : séquences de mots.

Le dictionnaire est volontairement large et multilingue (fr, en, es, it, de,
pt, arabe translittéré). Ajoute/retire des termes selon ta modération.
"""
import re
import unicodedata

_LEET = str.maketrans(
    {
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
        "8": "b", "9": "g", "@": "a", "$": "s", "€": "e", "!": "i",
        "|": "i", "£": "l", "+": "t",
    }
)


def _collapse(text: str) -> str:
    """Réduit les lettres répétées : 'coooonnard' -> 'conard'."""
    return re.sub(r"(.)\1+", r"\1", text)


def normalize(text: str) -> str:
    """Minuscule, sans accents, leet appliqué, lettres uniquement, réduit."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().translate(_LEET)
    text = re.sub(r"[^a-z]+", " ", text)
    return _collapse(text).strip()


# --------------------------------------------------------------------------- #
# Dictionnaire — mots entiers (+ pluriel)
# --------------------------------------------------------------------------- #
_RAW_WORDS = [
    # --- Français (courts / ambigus, mot entier uniquement) ---
    "con", "conne", "cone", "sal", "salaud", "salaude", "pute", "putes",
    "pouffe", "salope", "salopes", "merde", "merdes", "merdique", "merdeux",
    "emmerdeur", "chiant", "chiotte", "pd", "pede", "tapette", "tarlouze",
    "gouine", "folle", "mongol", "gogol", "debile", "abruti", "abrutie",
    "cretin", "cretine", "idiot", "idiote", "imbecile", "cave", "bouffon",
    "boufon", "blaireau", "clochard", "cassos", "casos", "bolos", "boloss",
    "tocard", "guignol", "nabot", "naze", "loser", "raté", "rate", "cul",
    "trouduc", "ducon", "pignouf", "gland", "glandu", "tanche", "truie",
    "grognasse", "greluche", "morue", "thon", "cageot", "boudin", "chieur",
    # --- Anglais ---
    "ass", "asses", "arse", "arses", "cock", "cocks", "dick", "dicks",
    "dyke", "fag", "fags", "hoe", "hoes", "slut", "sluts", "twat", "twats",
    "prick", "pricks", "git", "tosser", "wanker", "wankers", "skank",
    "douche", "douchebag", "jackass", "dumbass", "dipshit", "moron",
    "morons", "idiots", "loser", "losers", "retarded", "spastic", "nonce",
    "bellend", "knob", "knobhead", "minger", "munter", "slag", "tart",
    "hooker", "whore", "whores", "bimbo", "cuck", "simp", "incel",
    # --- Espagnol ---
    "puta", "putas", "puto", "putos", "cono", "zorra", "zorras", "polla",
    "verga", "pendejo", "pendeja", "mamon", "mamada", "mierda", "joder",
    "capullo", "gilipollas", "cabron", "cabrona", "maricon", "marica",
    "perra", "chocho", "gonorrea", "malparido",
    # --- Italien ---
    "cazzo", "cazzi", "culo", "troia", "troie", "puttana", "stronzo",
    "stronza", "coglione", "coglioni", "vaffanculo", "merda", "bastardo",
    "figa", "minchia", "porca", "zoccola", "sfigato",
    # --- Allemand ---
    "fotze", "arsch", "arschloch", "wichser", "schlampe", "hure", "hurensohn",
    "scheisse", "scheiss", "miststuck", "trottel", "spast", "spasti",
    # --- Portugais ---
    "caralho", "porra", "merda", "puta", "cu", "corno", "cornos", "buceta",
    "foda", "foder", "vagabunda", "otario", "babaca", "arrombado", "viado",
    # --- Arabe translittéré (courant en chat FR) ---
    "zeb", "zebi", "kahba", "kahbe", "charmuta", "sharmuta", "kelb", "hmar",
    "walou", "chwaya", "nique", "niquer", "niker", "tebe", "teub",
    # --- Slurs (à filtrer) ---
    "negro", "negre", "negresse", "niger", "niga", "nigga", "bougnoule",
    "bougnoul", "bicot", "raton", "feuj", "youpin", "youtre", "rital",
    "chinetoque", "niakoue", "melon", "gogole", "triso", "triso", "nazi",
    "chink", "spic", "kike", "wop", "paki", "coon", "gook", "wetback",
    "tranny", "faggot", "faggots", "cunt", "cunts",
]

# --------------------------------------------------------------------------- #
# Dictionnaire — racines (sous-chaîne d'un mot), termes longs et peu ambigus
# --------------------------------------------------------------------------- #
_RAW_ROOTS = [
    # Français
    "connard", "connasse", "conard", "conasse", "salopard", "salopiaud",
    "enculer", "encule", "enfoire", "enfoire", "batard", "putain",
    "pouffiasse", "poufiasse", "trouduc", "branleur", "branler", "raclure",
    "sousmerde", "peteux",
    # Anglais
    "fuck", "fucker", "fucking", "motherfucker", "shit", "bullshit",
    "bitch", "asshole", "asswipe", "bastard", "cocksucker",
    "bollocks", "wanker", "shithead", "dumbfuck", "jerkoff",
    # Espagnol
    "gilipollas", "cabron", "pendejo", "maricon", "chingar", "chinga",
    "hijoputa", "hijodeputa", "malparido", "cabronazo",
    # Italien
    "cazzo", "stronzo", "puttana", "vaffanculo", "coglione", "figliodiputtana",
    # Allemand
    "arschloch", "hurensohn", "wichser", "schlampe", "scheisse", "miststuck",
    # Portugais
    "caralho", "buceta", "arrombado", "filhodaputa", "vagabunda",
    # Arabe translittéré
    "charmuta", "sharmuta", "hmarr",
]

# --------------------------------------------------------------------------- #
# Dictionnaire — expressions (séquences de mots)
# --------------------------------------------------------------------------- #
_RAW_PHRASES = [
    "ta gueule", "ferme ta gueule", "ferme la", "nique ta mere",
    "niquer ta mere", "nique ta race", "fils de pute", "fille de pute",
    "fils de chien", "fils de chienne", "trou du cul", "trou de balle",
    "va te faire encule", "va te faire foutre", "va te faire mettre",
    "sac a merde", "tas de merde", "sous merde", "pauvre merde",
    "espece de merde", "sale merde", "grosse merde",
    "son of a bitch", "piece of shit", "fuck you", "fuck off", "go to hell",
    "hijo de puta", "hijo de perra", "la concha de tu madre",
    "figlio di puttana", "vai a cagare", "porco dio",
    "filho da puta", "vai tomar no cu",
]


def _build(raw: list[str]) -> set[str]:
    result = set()
    for entry in raw:
        norm = normalize(entry)
        if norm:
            result.add(norm.replace(" ", ""))
    return result


_WORDS = _build(_RAW_WORDS)
_ROOTS = _build(_RAW_ROOTS)
_PHRASES = [normalize(p) for p in _RAW_PHRASES if normalize(p)]


def _matches_word(token: str) -> bool:
    if token in _WORDS:
        return True
    # Tolérance pluriel / suffixes simples.
    for suffix in ("s", "es", "x"):
        if token.endswith(suffix) and token[: -len(suffix)] in _WORDS:
            return True
    return False


def _token_hit(token: str) -> str | None:
    if _matches_word(token):
        return token
    for root in _ROOTS:
        if root in token:
            return root
    return None


def find_insult(text: str) -> str | None:
    """Renvoie l'insulte détectée dans le texte, ou None."""
    norm = normalize(text)
    if not norm:
        return None
    tokens = norm.split()

    # 1) Mot entier ou racine à l'intérieur d'un mot.
    for token in tokens:
        hit = _token_hit(token)
        if hit:
            return hit

    # 2) Lettres espacées : on recolle les suites de lettres seules.
    merged, group = [], []
    for token in tokens:
        if len(token) == 1:
            group.append(token)
        else:
            if group:
                merged.append(_collapse("".join(group)))
                group = []
    if group:
        merged.append(_collapse("".join(group)))
    for word in merged:
        hit = _token_hit(word)
        if hit:
            return hit

    # 3) Expressions (séquence de mots).
    padded = f" {norm} "
    for phrase in _PHRASES:
        if f" {phrase} " in padded:
            return phrase

    return None
