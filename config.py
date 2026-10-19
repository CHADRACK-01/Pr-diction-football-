import os

# =========================================================
# TELEGRAM
# =========================================================
TOKEN = "8443191637:AAGcCknBZDg1o0NBeL8czLt0SsQ4c2LEMvY"

# Configuration du Canal Telegram
CANAL_ID = -1003999473611
CANAL_USERNAME = "@pronosticsfootball01"
CANAL_LIEN = "https://t.me/pronosticsfootball01"

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

try:
    os.makedirs(DOSSIER_PASSE, exist_ok=True)
    os.makedirs(DOSSIER_ACTUEL, exist_ok=True)
except Exception as e:
    print(f"⚠️ Impossible de créer les dossiers : {e}")

# =========================================================
# CHAMPIONNATS & COMPÉTITIONS
# =========================================================
# Clé technique : Nom exact pour le modèle IA
CHAMPIONNATS = {
    "premier_league": "Premier League", "laliga": "La Liga", "ligue_1": "Ligue 1",
    "bundesliga_1": "Bundesliga", "serie_a": "Serie A",
    "champions_league": "Champions League", "europa_league": "Europa League",
    "conference_league": "Conference League",
    "championship": "Championship", "league_one": "League One", "league_two": "League Two",
    "segunda_division": "Segunda Division", "serie_b": "Serie B", "ligue_2": "Ligue 2",
    "bundesliga_2": "2. Bundesliga", "super_lig": "Super Lig", "primeira_liga": "Primeira Liga",
    "eredivisie": "Eredivisie", "first_division_a": "First Division A",
    "super_league": "Super League", "premiership": "Premiership"
}

# ⚠️ NOUVEAU : Dictionnaire pour l'affichage (Pays/Zone + Emoji)
INFOS_COMPETITIONS = {
    "Premier League": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "Championship": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "League One": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "League Two": {"pays": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    
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
    
    "Super Lig": {"pays": "Turquie", "emoji": "🇹🇷"},
    "Primeira Liga": {"pays": "Portugal", "emoji": "🇵🇹"},
    "Eredivisie": {"pays": "Pays-Bas", "emoji": "🇳🇱"},
    "First Division A": {"pays": "Belgique", "emoji": "🇧🇪"},
    "Super League": {"pays": "Grèce", "emoji": "🇬🇷"},
    "Premiership": {"pays": "Écosse", "emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
}

# =========================================================
# BASE DE DONNÉES POSTGRESQL (AIVEN)
# =========================================================
DB_HOST = os.environ.get("DB_HOST", "").strip()
DB_PORT = os.environ.get("DB_PORT", "5432").strip()
DB_USER = os.environ.get("DB_USER", "").strip()
DB_PASSWORD = os.environ.get("DB_PASSWORD", "").strip()
DB_NAME = os.environ.get("DB_NAME", "").strip()

# =========================================================
# UPSTASH BLOB (stockage CSV)
# =========================================================
UPSTASH_BLOB_TOKEN = os.environ.get("UPSTASH_BLOB_TOKEN", "").strip()
UPSTASH_BUCKET_NAME = "PredictionFootball-csv"

# =========================================================
# API FOOTBALL-DATA & BZZOIRO
# =========================================================
FOOTBALL_DATA_KEY = "5a7a6a3afcca4bc88400d73a0e394588"
BZZOIRO_API_KEY = "83e607ea69471dd01e82cba1457b2b67f0d7cfb5"

# =========================================================
# DEBUG
# =========================================================
print("=" * 60)
print(f"🔧 DB_HOST = '{DB_HOST}' | DB_NAME = '{DB_NAME}'")
print(f"🔧 DB_PASSWORD chargé : {'OUI' if DB_PASSWORD else 'NON'}")
print(f"🔧 CANAL_ID = {CANAL_ID}")
print(f"🔧 FOOTBALL_DATA_KEY chargé : {'OUI' if FOOTBALL_DATA_KEY else 'NON'}")
print(f"🔧 BZZOIRO_API_KEY chargé : {'OUI' if BZZOIRO_API_KEY else 'NON'}")
print(f"🏆 {len(CHAMPIONNATS)} compétitions configurées dans le bot.")
print("=" * 60)

# =========================================================
# LIMITES PAR DÉFAUT
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100
