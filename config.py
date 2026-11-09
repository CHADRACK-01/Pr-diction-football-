import os

# =========================================================
# TELEGRAM (Sécurisé via variables d'environnement)
# =========================================================
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CANAL_ID = int(os.environ.get("CANAL_ID", "-1003999473611"))
CANAL_USERNAME = os.environ.get("CANAL_USERNAME", "@pronosticsfootball01")
CANAL_LIEN = os.environ.get("CANAL_LIEN", "https://t.me/pronosticsfootball01")

# =========================================================
# DÉTECTION DE L'ENVIRONNEMENT
# =========================================================
if os.environ.get("RENDER") == "true":
    DOSSIER_BASE = "/tmp/data"
else:
    DOSSIER_BASE = "data"

# =========================================================
# CHEMINS
# =========================================================
DOSSIER_PASSE = os.path.join(DOSSIER_BASE, "archives_passe")
DOSSIER_ACTUEL = os.path.join(DOSSIER_BASE, "saison_actuelle")
FICHIER_HISTORIQUE = os.path.join(DOSSIER_BASE, "historique_pronostics.csv")

os.makedirs(DOSSIER_PASSE, exist_ok=True)
os.makedirs(DOSSIER_ACTUEL, exist_ok=True)

# =========================================================
# CHAMPIONNATS (Anciens codes -> Noms propres de nos modèles)
# =========================================================
# C'est ce mapping qui permet au bot de faire le lien
# entre les boutons (#PRONO_LIGUE_1) et nos modèles ("Ligue 1")
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

# On garde aussi CHAMPIONNATS pour l'affichage dans les menus
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
    "bundesliga_2": "2. Bundesliga"
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
# API FOOTBALL-DATA & BZZOIRO
# =========================================================
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
BZZOIRO_API_KEY = os.environ.get("BZZOIRO_API_KEY", "")

# =========================================================
# LIMITES PAR DÉFAUT
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100

# =========================================================
# MODE VITRINE (True = Bot bloqué sauf inscription, False = Bot complet)
# =========================================================
MODE_VITRINE = False
