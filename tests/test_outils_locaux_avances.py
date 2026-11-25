"""Tests des nouveaux outils locaux et socles tiers."""

from core.outils_locaux_avances import (
    construire_combine,
    detecter_match_nul,
    detecter_underdog,
    checklist_avant_pari,
    moderer_texte,
    evaluer_anti_spam,
)
from core.socles_tiers import AdaptateurIndisponible


def test_constructeur_combine_recherche_une_cote_cible():
    match = construire_combine([
        {"nom": "A", "cote": 1.5, "proba": 0.8},
        {"nom": "B", "cote": 1.8, "proba": 0.7},
    ], cote_cible=2.7)
    assert len(match["matchs"]) == 2


def test_match_nul_respecte_la_regle_configuree():
    assert detecter_match_nul(0.35, 3.40)["eligible"] is True
    assert detecter_match_nul(0.20, 3.40)["eligible"] is False


def test_underdog_repose_sur_proba_et_cote():
    assert detecter_underdog(0.25, 5.0)["eligible"] is True


def test_checklist_bloque_si_mise_trop_forte():
    resultat = checklist_avant_pari(
        {"composition_verifiee": True, "meteo_verifiee": True, "cote": 2},
        mise=100,
        bankroll=100,
    )
    assert resultat["pret"] is False


def test_moderation_rejette_lien_et_interdit():
    assert moderer_texte("Consulte https://example.com")["autorise"] is False
    assert moderer_texte("Bonjour tout le monde")["autorise"] is True


def test_anti_spam_detecte_6_messages_en_10_secondes():
    assert evaluer_anti_spam([1, 2, 3, 4, 5, 6], maintenant=10)["spam"] is True


def test_adaptateur_tiers_ne_qualifie_pas_une_action_de_reussie():
    adaptateur = AdaptateurIndisponible()
    assert adaptateur.verifier_reference()[0] is False
