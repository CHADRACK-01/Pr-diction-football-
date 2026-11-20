# tests/test_equipes.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.equipes import cle_canonique, doublons_probables, rapport_doublons

def test_casse_accents_suffixes():
    assert cle_canonique("Atlético Madrid") == cle_canonique("atletico madrid")
    assert cle_canonique("FC Barcelona") == cle_canonique("Barcelona")
    assert cle_canonique("Paris Saint-Germain FC") == cle_canonique("Paris Saint Germain")

def test_equipes_differentes_restent_separees():
    assert cle_canonique("Inter") != cle_canonique("Internacional")
    assert cle_canonique("Lazio") != cle_canonique("Leicester")

def test_doublons_detectes_sans_fusion():
    noms = ["Manchester City", "Manchester City FC", "Arsenal", "Lens"]
    dup = doublons_probables(noms)
    assert len(dup) == 1
    assert dup[list(dup)[0]] == ["Manchester City", "Manchester City FC"]
    assert "Arsenal" not in str(dup)

def test_abreviations_non_devinees():
    # Limite volontaire : « Man City » n'est PAS relié à « Manchester City ».
    # Ce lien relève de la table de correspondance, validée par un humain.
    assert doublons_probables(["Man City", "Manchester City"]) == {}

def test_nom_vide_ignore():
    assert cle_canonique("") == ""
    assert doublons_probables(["", None]) == {}

def test_rapport_sans_doublon():
    assert rapport_doublons(["Lens", "Lille"]) == "Aucun doublon probable détecté."

if __name__ == "__main__":
    n = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); n += 1; print("✅", nom)
    print(f"{n} tests OK")
