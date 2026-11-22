# tests/test_alerte_apis.py
import os, sys
import types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Journalisation neutralisée pour le test unitaire (évite les dépendances Telegram/Turso)
_logs = types.ModuleType("core.utils.logs")
_logs.log_info = lambda *a, **k: None
_logs.log_error = lambda *a, **k: None
_logs.log_warning = lambda *a, **k: None
sys.modules["core.utils.logs"] = _logs

from core import alerte_apis as aa


def _etat_initial():
    aa.reinitialiser_etat()


def test_une_seule_panne_n_alerte_pas():
    _etat_initial()
    assert aa.traiter_resultats({"A": False}) == []


def test_alerte_apres_seuil_puis_une_seule_fois():
    _etat_initial()
    aa.traiter_resultats({"A": False})
    msgs = aa.traiter_resultats({"A": False})
    assert len(msgs) == 1 and "A ne répond plus" in msgs[0]
    assert aa.traiter_resultats({"A": False}) == []  # pas de spam


def test_message_de_retablissement():
    _etat_initial()
    aa.traiter_resultats({"A": False})
    aa.traiter_resultats({"A": False})
    msgs = aa.traiter_resultats({"A": True})
    assert msgs == ["✅ A répond de nouveau."]


def test_un_succes_remet_le_compteur_a_zero():
    _etat_initial()
    aa.traiter_resultats({"A": False})
    aa.traiter_resultats({"A": True})
    assert aa.traiter_resultats({"A": False}) == []  # 1 seul échec : pas d'alerte


def test_verifier_apis_exception_compte_comme_panne():
    _etat_initial()
    def casse():
        raise RuntimeError("réseau")
    assert aa.verifier_apis({"X": casse, "Y": lambda: True}) == {"X": False, "Y": True}


def test_verifier_et_alerter_envoie_et_protege():
    _etat_initial()
    envoyes = []
    testeurs = {"B": lambda: False}
    aa.verifier_et_alerter(envoyes.append, testeurs)
    assert envoyes == []
    assert aa.verifier_et_alerter(envoyes.append, testeurs) == 1
    assert len(envoyes) == 1

    def envoi_casse(_):
        raise RuntimeError("telegram down")
    # ne doit pas lever d'exception
    assert aa.verifier_et_alerter(envoi_casse, {"B": lambda: True}) == 0
