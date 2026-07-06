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
    # ----------------------------------------------------------------------- #
    # Français — courts / ambigus, mot entier uniquement
    # ----------------------------------------------------------------------- #
    "con", "cons", "conne", "connes",
    "salaud", "salauds", "salaude", "salaudes",
    "pute", "putes",
    "pouffe", "pouffes", "pouf", "poufs",
    "salope", "salopes",
    "merde", "merdes", "merdique", "merdiques", "merdeux", "merdeuse",
    "merdeuses",
    "emmerdeur", "emmerdeurs", "emmerdeuse", "emmerdeuses",
    "chiant", "chiante", "chiants", "chiantes",
    "chiotte", "chiottes",
    "pd", "pds", "pede", "pedes", "pédé", "pédés",
    "tapette", "tapettes",
    "tarlouze", "tarlouzes",
    "gouine", "gouines",
    "folle", "folles",
    "mongol", "mongols", "mongole", "mongoles",
    "gogol", "gogols", "gogole", "gogoles",
    "debile", "debiles", "débile", "débiles",
    "abruti", "abrutis", "abrutie", "abruties",
    "cretin", "cretins", "cretine", "cretines",
    "crétin", "crétins", "crétine", "crétines",
    "idiot", "idiots", "idiote", "idiotes",
    "imbecile", "imbeciles", "imbécile", "imbéciles",
    "bouffon", "bouffons", "boufon", "boufons",
    "blaireau", "blaireaux",
    "clochard", "clochards", "clocharde", "clochardes",
    "cassos", "casos",
    "bolos", "boloss", "bolosse", "bolosses",
    "tocard", "tocards", "tocarde", "tocardes",
    "guignol", "guignols",
    "nabot", "nabots",
    "naze", "nazes",
    "loser", "losers",
    "raté", "ratés", "ratée", "ratées", "rate", "rates",
    "cul", "culs",
    "trouduc", "trouducs",
    "ducon", "ducons",
    "pignouf", "pignoufs",
    "gland", "glands", "glandu", "glandus",
    "tanche", "tanches",
    "grognasse", "grognasses",
    "greluche", "greluches",
    "boudin", "boudins",
    "chieur", "chieurs", "chieuse", "chieuses",
    "andouille", "andouilles",
    "couillon", "couillons", "couillonne", "couillonnes",
    "couille", "couilles",
    "branleur", "branleurs", "branleuse", "branleuses",
    "boulet", "boulets",
    "teubé", "teubés", "teube", "teubes",
    "demeuré", "demeurés", "demeuree", "demeurees", "demeurée", "demeurées",
    "attardé", "attardés", "attardée", "attardées", "attarde", "attardes",
    "taré", "tarés", "tarée", "tarées", "tare", "tares",
    "neuneu", "neuneus",

    # ----------------------------------------------------------------------- #
    # Anglais
    # ----------------------------------------------------------------------- #
    "ass", "asses",
    "arse", "arses",
    "cock", "cocks",
    "dick", "dicks",
    "prick", "pricks",
    "twat", "twats",
    "slut", "sluts",
    "whore", "whores",
    "hoe", "hoes",
    "hooker", "hookers",
    "bimbo", "bimbos",
    "skank", "skanks",
    "wanker", "wankers",
    "tosser", "tossers",
    "git", "gits",
    "douche", "douches",
    "douchebag", "douchebags",
    "jackass", "jackasses",
    "dumbass", "dumbasses",
    "dipshit", "dipshits",
    "shithead", "shitheads",
    "moron", "morons",
    "idiot", "idiots",
    "loser", "losers",
    "retard", "retards",
    "retarded",
    "spastic", "spastics",
    "nonce", "nonces",
    "bellend", "bellends",
    "knob", "knobs",
    "knobhead", "knobheads",
    "minger", "mingers",
    "munter", "munters",
    "slag", "slags",
    "tart", "tarts",
    "cuck", "cucks",
    "simp", "simps",
    "incel", "incels",
    "freak", "freaks",
    "creep", "creeps",
    "bastard", "bastards",

    # ----------------------------------------------------------------------- #
    # Espagnol
    # ----------------------------------------------------------------------- #
    "puta", "putas",
    "puto", "putos",
    "cono", "coño",
    "polla",
    "verga",
    "pendejo", "pendejos", "pendeja", "pendejas",
    "mamon", "mamón", "mamones",
    "mamada", "mamadas",
    "mierda", "mierdas",
    "joder",
    "capullo", "capullos",
    "gilipollas",
    "cabron", "cabrón", "cabrones",
    "cabrona", "cabronas",
    "maricon", "maricón", "maricones",
    "marica", "maricas",
    "perra", "perras",
    "chocho",
    "gonorrea",
    "malparido", "malparidos", "malparida", "malparidas",

    # ----------------------------------------------------------------------- #
    # Italien
    # ----------------------------------------------------------------------- #
    "cazzo", "cazzi",
    "culo", "culi",
    "troia", "troie",
    "puttana", "puttane",
    "stronzo", "stronzi",
    "stronza", "stronze",
    "coglione", "coglioni",
    "vaffanculo",
    "merda", "merde",
    "bastardo", "bastardi",
    "bastarda", "bastarde",
    "figa",
    "minchia",
    "zoccola", "zoccole",
    "sfigato", "sfigati",
    "sfigata", "sfigate",

    # ----------------------------------------------------------------------- #
    # Allemand
    # ----------------------------------------------------------------------- #
    "fotze",
    "arsch",
    "arschloch", "arschlöcher",
    "wichser",
    "schlampe", "schlampen",
    "hure", "huren",
    "hurensohn",
    "scheisse", "scheiße", "scheiss", "scheiß",
    "trottel",
    "spast", "spasti",

    # ----------------------------------------------------------------------- #
    # Portugais
    # ----------------------------------------------------------------------- #
    "caralho",
    "porra",
    "merda",
    "puta", "putas",
    "cu",
    "corno", "cornos",
    "buceta",
    "foda",
    "foder",
    "vagabunda", "vagabundas",
    "otario", "otário", "otarios", "otários",
    "babaca", "babacas",
    "arrombado", "arrombados",
    "viado", "viados",

    # ----------------------------------------------------------------------- #
    # Arabe / maghrébin translittéré courant en chat FR
    # ----------------------------------------------------------------------- #
    "zeb", "zebi",
    "kahba", "kahbe",
    "charmuta", "sharmuta",
    "kelb", "kalb",
    "hmar", "hmarr",
    "nique", "niquer",
    "nik", "niker",
    "tebe", "teub",

    # ----------------------------------------------------------------------- #
    # Slurs / haine — à filtrer en mot entier
    # ----------------------------------------------------------------------- #
    "negro", "nègre", "negre", "negresse", "négresse",
    "niger", "niga", "nigga",
    "bougnoule", "bougnoul",
    "bicot", "bicots",
    "raton", "ratons",
    "feuj", "feujs",
    "youpin", "youpins",
    "youtre", "youtres",
    "rital", "ritals",
    "chinetoque", "chinetoques",
    "niakoue", "niakoues",
    "gogole", "gogoles",
    "triso", "trisos",
    "nazi", "nazis",
    "chink", "chinks",
    "spic", "spics",
    "kike", "kikes",
    "wop", "wops",
    "paki", "pakis",
    "coon", "coons",
    "gook", "gooks",
    "wetback", "wetbacks",
    "tranny", "trannies",
    "fag", "fags",
    "faggot", "faggots",
    "dyke", "dykes",
    "cunt", "cunts",
]

# --------------------------------------------------------------------------- #
# Dictionnaire — racines, termes longs et peu ambigus
# --------------------------------------------------------------------------- #
_RAW_ROOTS = [
    # ----------------------------------------------------------------------- #
    # Français
    # ----------------------------------------------------------------------- #
    "connard",
    "connasse",
    "conard",
    "conasse",
    "salopard",
    "salopiaud",
    "enculer",
    "encule",
    "enculé",
    "enculée",
    "enfoire",
    "enfoiré",
    "enfoirée",
    "batard",
    "bâtard",
    "batarde",
    "bâtarde",
    "putain",
    "pouffiasse",
    "poufiasse",
    "trouduc",
    "branleur",
    "branleuse",
    "branler",
    "raclure",
    "sousmerde",
    "sous-merde",
    "peteux",
    "péteux",
    "emmerder",
    "emmerdeur",
    "emmerdeuse",
    "couillonn",
    "merdass",
    "bordel",
    "niqu",
    "nik",
    "baltringue",
    "clochardis",

    # ----------------------------------------------------------------------- #
    # Anglais
    # ----------------------------------------------------------------------- #
    "fuck",
    "fucker",
    "fucking",
    "motherfucker",
    "shit",
    "bullshit",
    "bitch",
    "asshole",
    "arsehole",
    "asswipe",
    "bastard",
    "cocksucker",
    "bollocks",
    "wanker",
    "shithead",
    "dumbfuck",
    "jerkoff",
    "dipshit",
    "dickhead",
    "fuckface",
    "fuckwit",
    "shitface",
    "shitbag",
    "scumbag",
    "slutty",

    # ----------------------------------------------------------------------- #
    # Espagnol
    # ----------------------------------------------------------------------- #
    "gilipollas",
    "cabron",
    "cabrón",
    "pendejo",
    "pendeja",
    "maricon",
    "maricón",
    "chingar",
    "chinga",
    "hijoputa",
    "hijodeputa",
    "malparido",
    "malparida",
    "cabronazo",

    # ----------------------------------------------------------------------- #
    # Italien
    # ----------------------------------------------------------------------- #
    "cazzo",
    "stronzo",
    "stronza",
    "puttana",
    "vaffanculo",
    "coglione",
    "figliodiputtana",

    # ----------------------------------------------------------------------- #
    # Allemand
    # ----------------------------------------------------------------------- #
    "arschloch",
    "hurensohn",
    "wichser",
    "schlampe",
    "scheisse",
    "scheiße",
    "miststuck",
    "miststück",

    # ----------------------------------------------------------------------- #
    # Portugais
    # ----------------------------------------------------------------------- #
    "caralho",
    "buceta",
    "arrombado",
    "filhodaputa",
    "vagabunda",

    # ----------------------------------------------------------------------- #
    # Arabe / maghrébin translittéré
    # ----------------------------------------------------------------------- #
    "charmuta",
    "sharmuta",
    "hmarr",
]

# --------------------------------------------------------------------------- #
# Dictionnaire — expressions, séquences de mots
# --------------------------------------------------------------------------- #
_RAW_PHRASES = [
    # ----------------------------------------------------------------------- #
    # Français — insultes directes / vulgarités
    # ----------------------------------------------------------------------- #
    "ta gueule",
    "ferme ta gueule",
    "ferme la",
    "ferme la bouche",
    "va te faire foutre",
    "va te faire mettre",
    "va te faire encule",
    "va te faire enculer",
    "va te faire niquer",
    "nique ta mere",
    "nique ta mère",
    "niquer ta mere",
    "niquer ta mère",
    "nique tes morts",
    "nique ta race",
    "nique ton pere",
    "nique ton père",
    "fils de pute",
    "fille de pute",
    "fils de chienne",
    "fils de chien",
    "trou du cul",
    "trou de balle",
    "face de cul",
    "sac a merde",
    "sac à merde",
    "tas de merde",
    "sous merde",
    "sous-merde",
    "pauvre merde",
    "espece de merde",
    "espèce de merde",
    "sale merde",
    "grosse merde",
    "petite merde",
    "gros con",
    "grosse conne",
    "sale con",
    "sale conne",
    "pauvre con",
    "pauvre conne",
    "espece de con",
    "espèce de con",
    "espece de connard",
    "espèce de connard",
    "espece de connasse",
    "espèce de connasse",
    "sale pute",
    "sale salope",
    "sale batard",
    "sale bâtard",
    "sale enculé",
    "sale encule",
    "sale enfoiré",
    "sale enfoire",
    "gros batard",
    "gros bâtard",
    "petit con",
    "petite conne",

    # ----------------------------------------------------------------------- #
    # Français — animaux uniquement avec contexte insultant
    # ----------------------------------------------------------------------- #
    "sale rat",
    "gros rat",
    "petit rat",
    "face de rat",
    "sale cafard",
    "gros cafard",
    "sale porc",
    "gros porc",
    "sale truie",
    "grosse truie",
    "sale chien",
    "sale chienne",
    "race de chien",
    "chien de la casse",
    "sale morue",
    "vieille morue",
    "gros thon",
    "sale thon",
    "grosse vache",
    "sale vache",
    "vieille vache",

    # ----------------------------------------------------------------------- #
    # Français — haine / discrimination en expression
    # ----------------------------------------------------------------------- #
    "sale pd",
    "sale pede",
    "sale pédé",
    "sale gouine",
    "sale tapette",
    "sale tarlouze",
    "sale negre",
    "sale nègre",
    "sale noir",
    "sale arabe",
    "sale juif",
    "sale musulman",
    "sale chinois",
    "sale asiatique",
    "retourne dans ton pays",

    # ----------------------------------------------------------------------- #
    # Anglais
    # ----------------------------------------------------------------------- #
    "son of a bitch",
    "piece of shit",
    "piece of crap",
    "fuck you",
    "fuck off",
    "go fuck yourself",
    "go to hell",
    "shut up",
    "shut the fuck up",
    "mother fucker",
    "motherfucker",
    "dumb fuck",
    "dumb ass",
    "dumbass",
    "stupid bitch",
    "little bitch",
    "dirty bitch",
    "stupid fuck",
    "fucking idiot",
    "fucking moron",
    "you asshole",
    "you bastard",
    "you cunt",
    "bloody hell",
    "eat shit",
    "eat my ass",
    "suck my dick",
    "suck a dick",
    "kiss my ass",

    # ----------------------------------------------------------------------- #
    # Espagnol
    # ----------------------------------------------------------------------- #
    "hijo de puta",
    "hija de puta",
    "hijo de perra",
    "hija de perra",
    "la concha de tu madre",
    "vete a la mierda",
    "vete al carajo",
    "me cago en tu madre",
    "pedazo de mierda",
    "cara de culo",

    # ----------------------------------------------------------------------- #
    # Italien
    # ----------------------------------------------------------------------- #
    "figlio di puttana",
    "figlia di puttana",
    "vai a cagare",
    "vai affanculo",
    "vai a fanculo",
    "porco dio",
    "porca madonna",
    "pezzo di merda",
    "testa di cazzo",
    "faccia di culo",

    # ----------------------------------------------------------------------- #
    # Allemand
    # ----------------------------------------------------------------------- #
    "halt die fresse",
    "fick dich",
    "leck mich",
    "du arschloch",
    "du hurensohn",
    "sohn einer hure",
    "stück scheisse",
    "stück scheiße",

    # ----------------------------------------------------------------------- #
    # Portugais
    # ----------------------------------------------------------------------- #
    "filho da puta",
    "filha da puta",
    "vai tomar no cu",
    "vai se foder",
    "vai para o caralho",
    "pedaço de merda",
    "cara de cu",
    "seu merda",

    # ----------------------------------------------------------------------- #
    # Arabe / maghrébin translittéré
    # ----------------------------------------------------------------------- #
    "nik mok",
    "nik omok",
    "nik omouk",
    "nique mok",
    "nique omok",
    "nique omouk",
    "nik ta mere",
    "nik ta mère",
    "niktamere",
    "weld kahba",
    "weld el kahba",
    "bent kahba",
    "ya kelb",
    "ya kalb",
    "ya hmar",
    "ya hmarr",
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
