# core/pic_erreurs.py
"""
Détection d'un pic d'erreurs (fonctionnalité 134).

- core/utils/logs.py appelle enregistrer_erreur() à chaque log_error
- evaluer_pic() compte les erreurs de la fenêtre glissante
- Une alerte est envoyée quand le seuil est atteint, une seule fois par pic.
  Le pic est considéré terminé quand le compte retombe sous la moitié du seuil.

Ce module n'importe rien de core/utils/logs.py, pour éviter les imports circulaires.
L'état est en mémoire : au redémarrage, un pic en cours peut être signalé à nouveau.
"""

import threading
import time
from collections import Counter, deque

SEUIL_DEFAUT = 20
FENETRE_DEFAUT_SEC = 300

_LOCK = threading.Lock()
_EVENEMENTS = deque(maxlen=5000)  # (timestamp, module)
_EN_PIC = False


def enregistrer_erreur(module, maintenant=None):
    """Enregistre une erreur. Appelé depuis log_error, ne doit jamais échouer."""
    t = time.time() if maintenant is None else maintenant
    with _LOCK:
        _EVENEMENTS.append((t, module or "BOT"))


def erreurs_recentes(fenetre_sec=FENETRE_DEFAUT_SEC, maintenant=None):
    """Retourne la liste des modules des erreurs dans la fenêtre glissante."""
    t = time.time() if maintenant is None else maintenant
    limite = t - fenetre_sec
    with _LOCK:
        return [m for (ts, m) in _EVENEMENTS if ts >= limite]


def evaluer_pic(seuil=SEUIL_DEFAUT, fenetre_sec=FENETRE_DEFAUT_SEC, maintenant=None):
    """Retourne un dict {nb, fenetre, top} si un nouveau pic commence, sinon None."""
    global _EN_PIC
    recentes = erreurs_recentes(fenetre_sec, maintenant)
    nb = len(recentes)

    if nb >= seuil and not _EN_PIC:
        _EN_PIC = True
        return {
            "nb": nb,
            "fenetre": fenetre_sec,
            "top": Counter(recentes).most_common(3),
        }
    if nb < max(1, seuil // 2):
        _EN_PIC = False
    return None


def controler_et_alerter(envoyer, seuil=SEUIL_DEFAUT, fenetre_sec=FENETRE_DEFAUT_SEC, maintenant=None):
    """Envoie une alerte si un pic commence. Retourne 1 si envoyée, sinon 0. Ne lève pas d'exception."""
    try:
        pic = evaluer_pic(seuil, fenetre_sec, maintenant)
        if not pic:
            return 0
        lignes = [
            f"🚨 Pic d'erreurs : {pic['nb']} erreurs en {pic['fenetre'] // 60} min.",
            "Modules les plus touchés :",
        ]
        for module, n in pic["top"]:
            lignes.append(f"• {module} : {n}")
        envoyer("\n".join(lignes))
        return 1
    except Exception:
        return 0


def _reinitialiser():
    """Remet l'état à zéro (tests)."""
    global _EN_PIC
    with _LOCK:
        _EVENEMENTS.clear()
    _EN_PIC = False
