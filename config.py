import os

# =========================================================
# DÉTECTION DE L'ENVIRONNEMENT
# =========================================================
if os.environ.get("RENDER") == "true":
    DOSSIER_BASE = "/data"
else:
    DOSSIER_BASE = "data"

# =========================================================
# CHEMINS
# =========================================================
DOSSIER_PASSE = os.path.join(DOSSIER_BASE, "archives_passe")
DOSSIER_ACTUEL = os.path.join(DOSSIER_BASE, "saison_actuelle")
FICHIER_UTILISATEURS = os.path.join(DOSSIER_BASE, "utilisateurs.csv")
FICHIER_HISTORIQUE = os.path.join(DOSSIER_BASE, "historique_pronostics.csv")
FICHIER_COMPTEURS = os.path.join(DOSSIER_BASE, "compteurs_jour.csv")

# Création automatique des dossiers
os.makedirs(DOSSIER_PASSE, exist_ok=True)
os.makedirs(DOSSIER_ACTUEL, exist_ok=True)

# =========================================================
# LIMITES PAR STATUT
# =========================================================
LIMITE_FREE_JOUR = 3
LIMITE_PREMIUM_JOUR = 100
