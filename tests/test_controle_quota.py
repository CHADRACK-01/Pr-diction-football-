# tests/test_controle_quota.py
import os, sys, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_logs = types.ModuleType("core.utils.logs")
_logs.log_info = lambda *a, **k: None
_logs.log_error = lambda *a, **k: None
_logs.log_warning = lambda *a, **k: None
sys.modules["core.utils.logs"] = _logs

from core import controle_quota as cq


def test_evaluer_seuil_et_limites():
    conso = [
        {"cle": 1, "used": 80, "limit": 100},   # 80 % : atteint
        {"cle": 2, "used": 79, "limit": 100},   # 79 % : pas atteint
        {"cle": 3, "used": 5, "limit": 0},      # limite inconnue : ignorée
    ]
    r = cq.evaluer(conso)
    assert [d["cle"] for d in r] == [1]


def test_alerte_une_fois_par_jour_par_cle():
    vus = set()
    envoyes = []
    lecteur = lambda: [{"cle": 1, "used": 95, "limit": 100}]
    deja = lambda c: c in vus
    marque = lambda c: vus.add(c)
    assert cq.controler_et_alerter(envoyes.append, lecteur, deja, marque) == 1
    assert cq.controler_et_alerter(envoyes.append, lecteur, deja, marque) == 0
    assert len(envoyes) == 1 and "95/100" in envoyes[0]


def test_pas_d_alerte_sous_le_seuil():
    envoyes = []
    lecteur = lambda: [{"cle": 1, "used": 10, "limit": 100}]
    assert cq.controler_et_alerter(envoyes.append, lecteur, lambda c: False, lambda c: None) == 0
    assert envoyes == []


def test_lecture_en_erreur_ne_leve_pas():
    def casse():
        raise RuntimeError("réseau")
    assert cq.controler_et_alerter(lambda t: None, casse, lambda c: False, lambda c: None) == 0


def test_echec_d_envoi_n_empeche_pas_les_autres_cles():
    envoyes = []
    def envoi(t):
        if "clé 1" in t or "Clé API-Football 1" in t:
            raise RuntimeError("telegram")
        envoyes.append(t)
    lecteur = lambda: [
        {"cle": 1, "used": 90, "limit": 100},
        {"cle": 2, "used": 99, "limit": 100},
    ]
    n = cq.controler_et_alerter(envoi, lecteur, lambda c: False, lambda c: None)
    assert n == 1 and len(envoyes) == 1 and "99/100" in envoyes[0]
