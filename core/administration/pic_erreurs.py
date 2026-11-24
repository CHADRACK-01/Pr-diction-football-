# core/administration/pic_erreurs.py
"""
Détection d'un pic d'erreurs (fonctionnalité 134).

- ``core/utils/logs.py`` appelle :func:`enregistrer_erreur` à chaque ``log_error``.
- :func:`evaluer_pic` compte les erreurs de la fenêtre glissante.
- Une alerte est envoyée quand le seuil est atteint, une seule fois par pic.
  Le pic est considéré terminé quand le compte retombe sous la moitié du seuil.

Ce module n'importe rien de ``core/utils/logs.py`` pour éviter les imports
circulaires. L'état est en mémoire : au redémarrage, un pic en cours peut
être signalé à nouveau.
"""

from __future__ import annotations

import threading
import time
from collections import Counter, deque
from typing import Optional

SEUIL_DEFAUT = 20
FENETRE_DEFAUT_SEC = 300

_LOCK = threading.Lock()
_EVENEMENTS: deque[tuple[float, str]] = deque(maxlen=5000)  # (timestamp, module)
_EN_PIC = False


def enregistrer_erreur(module: str, maintenant: float | None = None) -> None:
    """Enregistre une erreur. Appelé depuis log_error, ne doit jamais échouer.

    Args:
        module: Nom du module émetteur de l'erreur.
        maintenant: Timestamp optionnel (pour les tests). Défaut : time.time().
    """
    t = time.time() if maintenant is None else maintenant
    with _LOCK:
        _EVENEMENTS.append((t, module or "BOT"))


def erreurs_recentes(
    fenetre_sec: int = FENETRE_DEFAUT_SEC,
    maintenant: float | None = None,
) -> list[str]:
    """Retourne la liste des modules des erreurs dans la fenêtre glissante.

    Args:
        fenetre_sec: Durée de la fenêtre en secondes.
        maintenant: Timestamp optionnel (pour les tests).

    Returns:
        Liste des noms de modules ayant émis des erreurs dans la fenêtre.
    """
    t = time.time() if maintenant is None else maintenant
    limite = t - fenetre_sec
    with _LOCK:
        return [m for (ts, m) in _EVENEMENTS if ts >= limite]


def evaluer_pic(
    seuil: int = SEUIL_DEFAUT,
    fenetre_sec: int = FENETRE_DEFAUT_SEC,
    maintenant: float | None = None,
) -> dict | None:
    """Détecte si un nouveau pic d'erreurs commence.

    Args:
        seuil: Nombre d'erreurs minimum dans la fenêtre pour déclarer un pic.
        fenetre_sec: Durée de la fenêtre glissante en secondes.
        maintenant: Timestamp optionnel (pour les tests).

    Returns:
        Dictionnaire {'nb', 'fenetre', 'top'} si un nouveau pic commence,
        sinon None.
    """
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


def controler_et_alerter(
    envoyer: object,
    seuil: int = SEUIL_DEFAUT,
    fenetre_sec: int = FENETRE_DEFAUT_SEC,
    maintenant: float | None = None,
) -> int:
    """Envoie une alerte si un pic commence.

    Retourne 1 si une alerte a été envoyée, 0 sinon. Ne lève jamais d'exception.

    Args:
        sender: Callable acceptant une chaîne de texte (ex: bot.send_message
                ou une fonction de log).
        seuil: Seuil d'erreurs pour déclarer un pic.
        fenetre_sec: Durée de la fenêtre en secondes.
        maintenant: Timestamp optionnel (pour les tests).

    Returns:
        Nombre d'alertes envoyées (0 ou 1).
    """
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


def _reinitialiser() -> None:
    """Remet l'état à zéro (réservé aux tests)."""
    global _EN_PIC
    with _LOCK:
        _EVENEMENTS.clear()
    _EN_PIC = False
