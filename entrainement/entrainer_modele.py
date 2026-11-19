# =====================================================================
# ENTRAÎNEMENT DU MODÈLE — À lancer dans Google Colab (ou en local)
#
# Ce script :
#   1. lit tous les matchs dans Turso ;
#   2. calcule les features EXACTEMENT comme le bot (core/features.py),
#      en n'utilisant que les matchs passés pour chaque match ;
#   3. entraîne un modèle 1N2 sur la période ancienne et le teste sur la
#      période récente (découpage dans le temps, pas aléatoire) ;
#   4. compare le modèle à deux références : la fréquence des résultats et
#      le marché des cotes (si disponible) ;
#   5. écrit le bundle dans models_cache, au format du contrat.
#
# AVANT DE LANCER (dans Colab, cellule 1) :
#   !pip install -q libsql scikit-learn numpy
#   !git clone https://github.com/<TON_COMPTE>/<TON_DEPOT>.git
#   (si le dépôt est privé, utilise un token GitHub dans l'URL, ou
#    téléverse les dossiers core/ dans /content)
#
# Variables à définir dans Colab (cellule 2) :
#   import os
#   os.environ["TURSO_URL"]   = "libsql://....turso.io"
#   os.environ["TURSO_TOKEN"] = "nouveau_token_régénéré"
#   REPO = "/content/<TON_DEPOT>"
#
# Puis lancer ce fichier (ou copier son contenu dans une cellule).
# =====================================================================
import os
import sys
import base64
import pickle
import datetime as dt

import numpy as np

REPO = os.environ.get("REPO", "/content/Pr-diction-football--main")
sys.path.insert(0, REPO)

from core.contrat_modele import FEATURE_NAMES, VERSION_CONTRAT, encoder_bundle
from core.features import EtatEquipes

import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss

TURSO_URL = os.environ["TURSO_URL"]
TURSO_TOKEN = os.environ["TURSO_TOKEN"]
PART_TEST = 0.2                       # 20 % les plus récents pour le test
CLASSES = {"H": 0, "D": 1, "A": 2}    # même convention que le bot

# -----------------------------------------------------------------
# 1. Lecture des matchs
# -----------------------------------------------------------------
import libsql

conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
lignes = conn.execute(
    """
    SELECT date, home_team, away_team, fthg, ftag, ftr, b365h, b365d, b365a
    FROM matchs
    WHERE fthg IS NOT NULL AND ftag IS NOT NULL AND ftr IS NOT NULL
    ORDER BY date, id
    """
).fetchall()
print(f"Matchs lus : {len(lignes)}")

matchs = []
for r in lignes:
    matchs.append({
        "date": str(r[0])[:10], "home": r[1], "away": r[2],
        "fthg": int(r[3]), "ftag": int(r[4]), "ftr": r[5],
        "cotes": (r[6], r[7], r[8]),
    })

# -----------------------------------------------------------------
# 2. Features sans fuite : snapshot AVANT mise à jour, pour chaque match
# -----------------------------------------------------------------
etat = EtatEquipes()
X, y, cotes, dates = [], [], [], []
for m in matchs:
    f = etat.predire(m["home"], m["away"], m["date"])
    if f is not None and m["ftr"] in CLASSES:
        X.append([f[n] for n in FEATURE_NAMES])
        y.append(CLASSES[m["ftr"]])
        cotes.append(m["cotes"])
        dates.append(m["date"])
    etat.mettre_a_jour(m)     # APRÈS le snapshot : aucune fuite

X = np.array(X, dtype=float)
y = np.array(y)
print(f"Lignes d'entraînement : {len(y)}")
if len(y) < 500:
    raise SystemExit("Pas assez de données après le calcul des features.")

# -----------------------------------------------------------------
# 3. Découpage temporel
# -----------------------------------------------------------------
coupure = int(len(y) * (1 - PART_TEST))
X_tr, y_tr = X[:coupure], y[:coupure]
X_te, y_te = X[coupure:], y[coupure:]
cotes_te = cotes[coupure:]
print(f"Entraînement : {len(y_tr)} matchs jusqu'au {dates[coupure-1]}")
print(f"Test         : {len(y_te)} matchs du {dates[coupure]} au {dates[-1]}")

modele_test = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
modele_test.fit(X_tr, y_tr)
proba = modele_test.predict_proba(X_te)
if list(modele_test.classes_) != [0, 1, 2]:
    raise SystemExit("Une classe est absente de l'entraînement : données insuffisantes.")

# -----------------------------------------------------------------
# 4. Métriques et références
# -----------------------------------------------------------------
def brier_1x2(p, cible):
    onehot = np.eye(3)[cible]
    return float(np.mean(np.sum((p - onehot) ** 2, axis=1)))

freq = np.bincount(y_tr, minlength=3) / len(y_tr)
proba_freq = np.tile(freq, (len(y_te), 1))

metriques = {
    "1N2": {
        "accuracy": float(accuracy_score(y_te, proba.argmax(axis=1))),
        "log_loss": float(log_loss(y_te, proba, labels=[0, 1, 2])),
        "brier": brier_1x2(proba, y_te),
        "n_test": int(len(y_te)),
    },
    "ref_frequence": {
        "log_loss": float(log_loss(y_te, proba_freq, labels=[0, 1, 2])),
        "brier": brier_1x2(proba_freq, y_te),
    },
}

# Marché : probabilités implicites des cotes B365, normalisées (marge retirée)
cotes_valides = [(i, c) for i, c in enumerate(cotes_te) if all(v and v > 1 for v in c)]
if cotes_valides:
    idx = np.array([i for i, _ in cotes_valides])
    brut = np.array([[1 / v for v in c] for _, c in cotes_valides])
    proba_marche = brut / brut.sum(axis=1, keepdims=True)
    metriques["ref_marche"] = {
        "log_loss": float(log_loss(y_te[idx], proba_marche, labels=[0, 1, 2])),
        "brier": brier_1x2(proba_marche, y_te[idx]),
        "n": int(len(idx)),
    }
    metriques["1N2_sur_meme_echantillon"] = {
        "log_loss": float(log_loss(y_te[idx], proba[idx], labels=[0, 1, 2])),
        "brier": brier_1x2(proba[idx], y_te[idx]),
    }

print("\n=== RÉSULTATS SUR LA PÉRIODE DE TEST ===")
for nom, m in metriques.items():
    print(nom, {k: round(v, 4) if isinstance(v, float) else v for k, v in m.items()})
print("Lecture : le modèle n'est utile que s'il fait mieux que ref_frequence")
print("ET, si ref_marche existe, qu'il fait mieux (ou presque) que le marché.")

# -----------------------------------------------------------------
# 5. Modèle final : entraîné sur TOUTES les données
# -----------------------------------------------------------------
modele_final = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
modele_final.fit(X, y)

bundle = {
    "schema_version": VERSION_CONTRAT,
    "feature_names": list(FEATURE_NAMES),
    "models": {"1N2": modele_final},
    "metrics": metriques,
    "etat": etat.vers_dict(),                 # état après TOUS les matchs
    "date_max_donnees": etat.date_max,
    "date_entrainement": dt.datetime.now().isoformat(timespec="seconds"),
    "total_matchs": int(len(y)),
    "versions": {"sklearn": sklearn.__version__, "numpy": np.__version__},
}

# -----------------------------------------------------------------
# 6. Écriture dans models_cache (le bot lit la dernière ligne)
# -----------------------------------------------------------------
donnees = encoder_bundle(bundle)
conn.execute("INSERT INTO models_cache (data) VALUES (?)", (donnees,))
conn.commit()
print(f"\n✅ Modèle écrit dans models_cache ({len(donnees)//1024} Ko), "
      f"données jusqu'au {etat.date_max}")
print(f"⚠️  Version scikit-learn utilisée : {sklearn.__version__} "
      f"(mets-la dans requirements.txt : scikit-learn=={sklearn.__version__})")
