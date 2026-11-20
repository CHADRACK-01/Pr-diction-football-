# tests/test_libelles_confiance.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.libelles_confiance import phrase_probabilite

def test_plus_de_mot_certitude():
    assert "certitude" not in phrase_probabilite(76.7).lower()

def test_courte_et_renvoie_au_bilan():
    t = phrase_probabilite(76.7)
    assert "/bilan" in t and "76.7%" in t and "garantie" not in t.lower()

def test_valeur_invalide_vide():
    assert phrase_probabilite(None) == ""
    assert phrase_probabilite("abc") == ""

def test_balises_html_equilibrees():
    t = phrase_probabilite(50)
    assert t.count("<b>") == t.count("</b>") == 1

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
