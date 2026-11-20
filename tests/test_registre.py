# tests/test_registre.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.registre import empreinte_donnees, empreinte_modele, bloc_registre

LIGNES = [
    ("2024-01-01", "Lens", "Lille", 2, 1, "H"),
    ("2024-01-02", "Nice", "Lyon", 0, 0, "D"),
]

def test_meme_donnees_meme_empreinte():
    assert empreinte_donnees(LIGNES) == empreinte_donnees(list(LIGNES))

def test_ordre_sans_importance():
    assert empreinte_donnees(LIGNES) == empreinte_donnees(list(reversed(LIGNES)))

def test_un_seul_resultat_change_lempreinte():
    modifie = [("2024-01-01", "Lens", "Lille", 2, 1, "D")] + LIGNES[1:]
    assert empreinte_donnees(LIGNES) != empreinte_donnees(modifie)

def test_ajout_dun_match_change_lempreinte():
    assert empreinte_donnees(LIGNES) != empreinte_donnees(LIGNES + [("2024-01-03", "A", "B", 1, 0, "H")])

def test_empreinte_modele_stable():
    assert empreinte_modele("abc") == empreinte_modele(b"abc")
    assert empreinte_modele("abc") != empreinte_modele("abd")

def test_bloc_contient_tout_ce_qui_est_necessaire_a_la_reproduction():
    bloc = bloc_registre(LIGNES, {"PART_TEST": 0.2, "ELO_K": 32.0}, {"sklearn": "1.6.1"})
    assert bloc["nb_matchs"] == 2
    assert bloc["parametres"]["ELO_K"] == 32.0
    assert bloc["versions"]["sklearn"] == "1.6.1"
    assert len(bloc["empreinte_donnees"]) == 16

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
