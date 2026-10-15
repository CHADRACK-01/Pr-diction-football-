import os

# =========================================================
# DÉTECTION DE L'ENVIRONNEMENT
# =========================================================
if os.environ.get("RENDER") == "true":
    DOSSIER_BASE = "/tmp/data"
else:
    DOSSIER_BASE = "data"

# =========================================================
# CHEMINS (pour fichiers temporaires locaux uniquement)
# =========================================================
DOSSIER_PASSE = os.path.join(DOSSIER_BASE, "archives_passe")
DOSSIER_ACTUEL = os.path.join(DOSSIER_BASE, "saison_actuelle")
FICHIER_HISTORIQUE = os.path.join(DOSSIER_BASE, "historique_pronostics.csv")

# Création automatique des dossiers
try:
    os.makedirs(DOSSIER_PASSE, exist_ok=True)
    os.makedirs(DOSSIER_ACTUEL, exist_ok=True)
except Exception as e:
    print(f"⚠️ Impossible de créer les dossiers : {e}")

# =========================================================
# CHAMPIONNATS
# =========================================================
CHAMPIONNATS = {
    "premier_league": "E0",
    "championship": "E1",
    "laliga": "SP1",
    "laliga_2": "SP2",
    "ligue_1": "F1",
    "ligue_2": "F2",
    "bundesliga_1": "D1",
    "bundesliga_2": "D2",
    "serie_a": "I1",
    "serie_b": "I2"
}

# =========================================================
# BASE DE DONNÉES POSTGRESQL (AIVEN)
# =========================================================
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")

# =========================================================
# LIMITES PAR STATUT
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100
