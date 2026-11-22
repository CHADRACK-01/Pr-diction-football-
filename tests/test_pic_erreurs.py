# tests/test_pic_erreurs.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import pic_erreurs as pe


def _neuf():
    pe._reinitialiser()


def test_sous_le_seuil_pas_d_alerte():
    _neuf()
    for i in range(5):
        pe.enregistrer_erreur("API", maintenant=1000 + i)
    assert pe.evaluer_pic(seuil=10, fenetre_sec=300, maintenant=1010) is None


def test_pic_declenche_une_seule_alerte():
    _neuf()
    for i in range(12):
        pe.enregistrer_erreur("DATABASE", maintenant=1000 + i)
    envoyes = []
    assert pe.controler_et_alerter(envoyes.append, seuil=10, fenetre_sec=300, maintenant=1011) == 1
    assert pe.controler_et_alerter(envoyes.append, seuil=10, fenetre_sec=300, maintenant=1012) == 0
    assert len(envoyes) == 1 and "12 erreurs" in envoyes[0] and "DATABASE : 12" in envoyes[0]


def test_fenetre_glissante_ignore_les_vieilles_erreurs():
    _neuf()
    for i in range(15):
        pe.enregistrer_erreur("X", maintenant=1000 + i)
    # 400 s plus tard, la fenêtre de 300 s ne contient plus rien
    assert pe.erreurs_recentes(300, maintenant=1400) == []


def test_nouveau_pic_apres_retour_au_calme():
    _neuf()
    for i in range(12):
        pe.enregistrer_erreur("A", maintenant=1000 + i)
    assert pe.evaluer_pic(seuil=10, fenetre_sec=300, maintenant=1011) is not None
    # calme : la fenêtre se vide, l'état repasse à "pas de pic"
    assert pe.evaluer_pic(seuil=10, fenetre_sec=300, maintenant=2000) is None
    for i in range(12):
        pe.enregistrer_erreur("A", maintenant=2000 + i)
    assert pe.evaluer_pic(seuil=10, fenetre_sec=300, maintenant=2011) is not None


def test_echec_envoi_ne_leve_pas():
    _neuf()
    for i in range(12):
        pe.enregistrer_erreur("A", maintenant=1000 + i)
    def casse(_):
        raise RuntimeError("telegram")
    assert pe.controler_et_alerter(casse, seuil=10, fenetre_sec=300, maintenant=1011) == 0
