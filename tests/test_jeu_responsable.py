# tests/test_jeu_responsable.py
import os, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stubs : on teste la logique sans base de données
stub_logs = types.ModuleType("core.utils.logs"); stub_logs.log_warning = lambda *a, **k: None
sys.modules["core.utils.logs"] = stub_logs
etat = {"actif": False}
stub_ff = types.ModuleType("core.feature_flags"); stub_ff.est_active = lambda fid: etat["actif"]
sys.modules["core.feature_flags"] = stub_ff

from core import jeu_responsable as jr

def test_inchange_si_interrupteur_eteint():
    etat["actif"] = False
    assert jr.ajouter_mention("<b>Bulletin</b>") == "<b>Bulletin</b>"

def test_mention_ajoutee_si_interrupteur_allume():
    etat["actif"] = True
    res = jr.ajouter_mention("<b>Bulletin</b>")
    assert res.startswith("<b>Bulletin</b>") and "Jeu responsable" in res

def test_texte_vide_inchange():
    etat["actif"] = True
    assert jr.ajouter_mention("") == ""
    assert jr.ajouter_mention(None) is None

def test_mention_html_valide():
    # Balises ouvertes = balises fermées (Telegram rejette le HTML mal formé)
    assert jr.MENTION_HTML.count("<i>") == jr.MENTION_HTML.count("</i>") == 1

if __name__ == "__main__":
    ok = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); ok += 1; print("✅", nom)
    print(f"{ok} tests OK")
