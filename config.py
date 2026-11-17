# config.py
"""
Configuration centralisée du bot.
Toutes les variables critiques sont lues depuis l'environnement.
Aucune clé API n'est stockée en dur dans le code (sécurité).
"""

import os
import sys

# =========================================================
# TELEGRAM
# =========================================================
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# ADMIN_ID : identifiant de l'admin principal (fallback sûr : le tien)
ADMIN_ID_RAW = os.environ.get("ADMIN_ID", "").strip()
try:
    ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else None
except (ValueError, TypeError):
    ADMIN_ID = None
try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except (ValueError, TypeError):
    ADMIN_ID = 8653408729

# CANAL_ID peut être un int négatif (-100...) ou un username (@canal)
CANAL_ID_RAW = os.environ.get("CANAL_ID", "").strip()
if CANAL_ID_RAW.startswith("@") or not CANAL_ID_RAW.startswith("-"):
    CANAL_ID = None
else:
    try:
        CANAL_ID = int(CANAL_ID_RAW)
    except (ValueError, TypeError):
        CANAL_ID = None
if CANAL_ID_RAW.startswith("@") or CANAL_ID_RAW.startswith("-") is False:
    CANAL_ID = CANAL_ID_RAW
else:
    try:
        CANAL_ID = int(CANAL_ID_RAW)
    except (ValueError, TypeError):
        CANAL_ID = -1003999473611

CANAL_USERNAME = os.environ.get("CANAL_USERNAME", "@pronosticsfootball01")
CANAL_LIEN = os.environ.get("CANAL_LIEN", "https://t.me/pronosticsfootball01")

# =========================================================
# MODES
# =========================================================
MODE_VITRINE = os.environ.get("MODE_VITRINE", "false").lower() == "true"
MODE_TEST = os.environ.get("MODE_TEST", "false").lower() == "true"

# =========================================================
# DÉTECTION DE L'ENVIRONNEMENT
# =========================================================
if os.environ.get("RENDER") == "true":
    DOSSIER_BASE = "/tmp/data"
else:
    DOSSIER_BASE = "data"

DOSSIER_PASSE = os.path.join(DOSSIER_BASE, "archives_passe")
DOSSIER_ACTUEL = os.path.join(DOSSIER_BASE, "saison_actuelle")
FICHIER_HISTORIQUE = os.path.join(DOSSIER_BASE, "historique_pronostics.csv")

try:
    os.makedirs(DOSSIER_PASSE, exist_ok=True)
    os.makedirs(DOSSIER_ACTUEL, exist_ok=True)
except OSError:
    pass

# =========================================================
# CHAMPIONNATS
# =========================================================
MAPPING_COMPETITIONS = {
    "premier_league": "Premier League",
    "championship": "Championship",
    "laliga": "La Liga",
    "segunda_division": "La Liga 2",
    "ligue_1": "Ligue 1",
    "ligue_2": "Ligue 2",
    "bundesliga_1": "Bundesliga",
    "bundesliga_2": "2. Bundesliga",
    "serie_a": "Serie A",
    "serie_b": "Serie B",
    "champions_league": "Ligue des Champions",
    "europa_league": "Europa League",
    "conference_league": "Conference League",
}

CHAMPIONNATS = {
    "premier_league": "Premier League",
    "laliga": "La Liga",
    "ligue_1": "Ligue 1",
    "bundesliga_1": "Bundesliga",
    "serie_a": "Serie A",
    "champions_league": "Champions League",
    "europa_league": "Europa League",
    "conference_league": "Conference League",
    "championship": "Championship",
    "ligue_2": "Ligue 2",
    "segunda_division": "Segunda Division",
    "serie_b": "Serie B",
    "bundesliga_2": "2. Bundesliga",
}

INFOS_COMPETITIONS = {
    "Premier League": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "Championship": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "La Liga": {"pays": "Espagne", "emoji": "🇪🇸"},
    "Segunda Division": {"pays": "Espagne", "emoji": "🇪🇸"},
    "Ligue 1": {"pays": "France", "emoji": "🇫🇷"},
    "Ligue 2": {"pays": "France", "emoji": "🇫🇷"},
    "Bundesliga": {"pays": "Allemagne", "emoji": "🇩🇪"},
    "2. Bundesliga": {"pays": "Allemagne", "emoji": "🇩🇪"},
    "Serie A": {"pays": "Italie", "emoji": "🇮🇹"},
    "Serie B": {"pays": "Italie", "emoji": "🇮🇹"},
    "Champions League": {"pays": "Europe", "emoji": "🇪🇺"},
    "Europa League": {"pays": "Europe", "emoji": "🇪🇺"},
    "Conference League": {"pays": "Europe", "emoji": "🇪🇺"},
}

# =========================================================
# TURSO (Base de données)
# =========================================================
TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")

# =========================================================
# APIs EXTERNES
# =========================================================
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
BZZOIRO_API_KEY = os.environ.get("BZZOIRO_API_KEY", "")

API_FOOTBALL_KEYS = [
    os.environ.get("API_FOOTBALL_KEY_1", ""),
    os.environ.get("API_FOOTBALL_KEY_2", ""),
]
API_FOOTBALL_KEYS = [k for k in API_FOOTBALL_KEYS if k]

# =========================================================
# LIMITES
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100

# =========================================================
# TAUX DE CHANGE (CDF par Star)
# =========================================================
TAUX_CDF_PAR_STAR = int(os.environ.get("TAUX_CDF_PAR_STAR", "40"))

# =========================================================
# LOGS TELEGRAM
# =========================================================
LOG_DEDUP_WINDOW_SEC = int(os.environ.get("LOG_DEDUP_WINDOW_SEC", "60"))
LOG_RECAP_INTERVAL_SEC = int(os.environ.get("LOG_RECAP_INTERVAL_SEC", "3600"))

# =========================================================
# VÉRIFICATION DES VARIABLES CRITIQUES
# =========================================================
def verifier_configuration():
    problemes = []
    if not TOKEN:
        problemes.append("TELEGRAM_TOKEN manquant ou vide")
    if not TURSO_URL:
        problemes.append("TURSO_URL manquant ou vide")
    if not TURSO_TOKEN:
        problemes.append("TURSO_TOKEN manquant ou vide")
    if ADMIN_ID is None:
        problemes.append("ADMIN_ID manquant ou invalide")
    if not CANAL_ID:
        problemes.append("CANAL_ID manquant ou invalide")

    if problemes:
        message = "❌ Configuration incomplète :\n" + "\n".join(f"  • {p}" for p in problemes)
        print(message, file=sys.stderr)
        raise RuntimeError(message)

    warnings = []
    if not FOOTBALL_DATA_KEY:
        warnings.append("FOOTBALL_DATA_KEY absent")
    if not BZZOIRO_API_KEY:
        warnings.append("BZZOIRO_API_KEY absent")
    if not API_FOOTBALL_KEYS:
        warnings.append("API_FOOTBALL_KEYS absent")

    for w in warnings:
        print(f"⚠️ {w}")
    return True
