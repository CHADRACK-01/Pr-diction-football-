# tests/test_backtest.py
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backtest import backtest, lire

def test_pari_gagnant_roi_exact():
    # Avantage sur H : 0.6*2.5-1 = 0.5 > seuil ; gagne -> gain 2.5, mise 1 -> ROI +150 %
    res = backtest([{"p": (0.6, 0.2, 0.2), "cotes": (2.5, 3.0, 3.0), "issue": "H"}])
    assert res["paris"] == 1 and res["gagnants"] == 1
    assert abs(res["roi"] - 1.5) < 1e-9

def test_pari_perdant_roi_moins_1():
    res = backtest([{"p": (0.6, 0.2, 0.2), "cotes": (2.5, 3.0, 3.0), "issue": "A"}])
    assert abs(res["roi"] - (-1.0)) < 1e-9

def test_aucun_pari_sous_le_seuil():
    # Avantage = 0.5*2.0-1 = 0 : pas de pari
    res = backtest([{"p": (0.5, 0.25, 0.25), "cotes": (2.0, 4.0, 4.0), "issue": "H"}])
    assert res["paris"] == 0 and res["roi"] is None
    assert "rien à conclure" in lire(res)

def test_donnees_invalides_ignorees():
    res = backtest([{"p": None, "cotes": (2, 3, 3), "issue": "H"},
                    {"p": (0.6, 0.2, 0.2), "cotes": ("?", 3, 3), "issue": "H"},
                    {"p": (0.6, 0.2, 0.2), "cotes": (2.5, 3, 3), "issue": "X"}])
    assert res["matchs_utiles"] == 0

def test_fiabilite_signalee_sous_300_paris():
    res = backtest([{"p": (0.6, 0.2, 0.2), "cotes": (2.5, 3.0, 3.0), "issue": "H"}] * 5)
    assert res["fiable"] is False
    assert "300" in lire(res)

def test_brier_marche_calcule():
    res = backtest([{"p": (0.5, 0.25, 0.25), "cotes": (2.0, 4.0, 4.0), "issue": "H"}])
    assert res["brier_marche"] is not None and res["brier_modele"] is not None

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
