# tests/test_alerte_apis.py
import json, os, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Journalisation neutralisée pour le test unitaire
_logs = types.ModuleType("core.utils.logs")
_logs.log_info = lambda *a, **k: None
_logs.log_error = lambda *a, **k: None
_logs.log_warning = lambda *a, **k: None
sys.modules["core.utils.logs"] = _logs

from core import alerte_apis as aa


def test_une_seule_panne_n_alerte_pas():
    e = aa.EtatEnMemoire()
    assert aa.traiter_resultats({"A": False}, e) == []


def test_alerte_apres_seuil_puis_une_seule_fois():
    e = aa.EtatEnMemoire()
    aa.traiter_resultats({"A": False}, e)
    msgs = aa.traiter_resultats({"A": False}, e)
    assert len(msgs) == 1 and "A ne répond plus" in msgs[0]
    assert aa.traiter_resultats({"A": False}, e) == []


def test_message_de_retablissement():
    e = aa.EtatEnMemoire()
    aa.traiter_resultats({"A": False}, e)
    aa.traiter_resultats({"A": False}, e)
    assert aa.traiter_resultats({"A": True}, e) == ["✅ A répond de nouveau."]


def test_un_succes_remet_le_compteur_a_zero():
    e = aa.EtatEnMemoire()
    aa.traiter_resultats({"A": False}, e)
    aa.traiter_resultats({"A": True}, e)
    assert aa.traiter_resultats({"A": False}, e) == []


def test_panne_deja_signalee_non_re_signalee_apres_redemarrage():
    # L'état persiste : une nouvelle "instance" (redémarrage) relit le même stockage
    stockage = aa.EtatEnMemoire()
    aa.traiter_resultats({"A": False}, stockage)
    aa.traiter_resultats({"A": False}, stockage)
    redemarrage = stockage  # même base, nouveau processus
    assert aa.traiter_resultats({"A": False}, redemarrage) == []


def test_exception_compte_comme_panne():
    def casse():
        raise RuntimeError("réseau")
    assert aa.verifier_apis({"X": casse, "Y": lambda: True}) == {"X": False, "Y": True}


def test_verifier_et_alerter_envoie_et_protege():
    e = aa.EtatEnMemoire()
    envoyes = []
    testeurs = {"B": lambda: False}
    aa.verifier_et_alerter(envoyes.append, testeurs, e)
    assert envoyes == []
    assert aa.verifier_et_alerter(envoyes.append, testeurs, e) == 1
    assert len(envoyes) == 1

    def envoi_casse(_):
        raise RuntimeError("telegram down")
    assert aa.verifier_et_alerter(envoi_casse, {"B": lambda: True}, e) == 0


def test_etat_en_base_lu_et_ecrit_au_format_json():
    # Simule users.admin.get_parametre / set_parametre
    faux_parametres = {}
    faux_admin = types.ModuleType("users.admin")
    faux_admin.get_parametre = lambda cle, defaut=None: faux_parametres.get(cle, defaut)
    faux_admin.set_parametre = lambda cle, valeur, description="": faux_parametres.__setitem__(cle, valeur) or True
    sys.modules["users.admin"] = faux_admin

    etat = aa.EtatEnBase()
    etat.ecrire("A", {"echecs": 2, "signale": True})
    assert json.loads(faux_parametres["api_etat_A"]) == {"echecs": 2, "signale": True}
    assert etat.lire("A") == {"echecs": 2, "signale": True}
    assert etat.lire("inconnue") == {"echecs": 0, "signale": False}
    faux_parametres["api_etat_A"] = "pas du json"
    assert etat.lire("A") == {"echecs": 0, "signale": False}
