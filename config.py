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
# CHAMPIONNATS
# =========================================================
CHAMPIONNATS = {
    "premier_league": "E0", "championship": "E1", "laliga": "SP1",
    "laliga_2": "SP2", "ligue_1": "F1", "ligue_2": "F2",
    "bundesliga_1": "D1", "bundesliga_2": "D2", "serie_a": "I1", "serie_b": "I2"
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
# API FOOTBALL-DATA
# =========================================================
FOOTBALL_DATA_KEY = "5a7a6a3afcca4bc88400d73a0e394588"

# =========================================================
# API BZZOIRO
# =========================================================
BZZOIRO_API_KEY = "83e607ea69471dd01e82cba1457b2b67f0d7cfb5"

# Debug
print("=" * 60)
print(f"🔧 DB_HOST = '{DB_HOST}' | DB_NAME = '{DB_NAME}'")
print(f"🔧 DB_PASSWORD chargé : {'OUI' if DB_PASSWORD else 'NON'}")
print(f"🔧 CANAL_ID = {CANAL_ID}")
print(f"🔧 FOOTBALL_DATA_KEY chargé : {'OUI' if FOOTBALL_DATA_KEY else 'NON'}")
print(f"🔧 BZZOIRO_API_KEY chargé : {'OUI' if BZZOIRO_API_KEY else 'NON'}")
print("=" * 60)

# =========================================================
# LIMITES PAR DÉFAUT
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100
