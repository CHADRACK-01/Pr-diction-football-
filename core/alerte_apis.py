# core/alerte_apis.py
"""
Alerte admin si une API de données ne répond plus (fonctionnalité 133).

- Vérifie chaque source via son tester_api()
- N'alerte qu'après SEUIL_ECHECS contrôles consécutifs en échec (évite les faux positifs)
- Une seule alerte par panne, puis un message de rétablissement
- L'état est gardé en mémoire : au redémarrage, une panne encore active
  sera signalée à nouveau une fois, ce qui est acceptable.
"""

from core.utils.logs import log_info, log_error

SEUIL_ECHECS = 2

_echecs = {}
_en_panne_signalee = set()


def _testeurs_par_defaut():
    from core.api import api_football, bzzoiro, openligadb, thesportsdb
    return {
        "API-Football": api_football.tester_api,
        "Bzzoiro": bzzoiro.tester_api,
        "OpenLigaDB": openligadb.tester_api,
        "TheSportsDB": thesportsdb.tester_api,
    }


def verifier_apis(testeurs=None):
    """Retourne {nom: bool}. Une exception compte comme une panne."""
    if testeurs is None:
        testeurs = _testeurs_par_defaut()
    resultats = {}
    for nom, testeur in testeurs.items():
        try:
            resultats[nom] = bool(testeur())
        except Exception:
            resultats[nom] = False
    return resultats


def traiter_resultats(resultats):
    """Met à jour les compteurs et retourne la liste des messages à envoyer."""
    messages = []
    for nom, ok in resultats.items():
        if ok:
            _echecs[nom] = 0
            if nom in _en_panne_signalee:
                _en_panne_signalee.discard(nom)
                messages.append(f"✅ {nom} répond de nouveau.")
        else:
            _echecs[nom] = _echecs.get(nom, 0) + 1
            if _echecs[nom] >= SEUIL_ECHECS and nom not in _en_panne_signalee:
                _en_panne_signalee.add(nom)
                messages.append(f"🚨 {nom} ne répond plus ({_echecs[nom]} contrôles en échec).")
    return messages


def verifier_et_alerter(envoyer, testeurs=None):
    """Contrôle les APIs et appelle envoyer(texte) s'il y a un changement d'état.

    Retourne le nombre de messages envoyés. Ne lève jamais d'exception.
    """
    try:
        resultats = verifier_apis(testeurs)
        messages = traiter_resultats(resultats)
    except Exception as e:
        log_error(message="Contrôle des APIs impossible", module="API", exception=e)
        return 0

    if not messages:
        return 0
    try:
        envoyer("\n".join(messages))
        log_info(f"Alerte APIs envoyée ({len(messages)} message(s))", "API")
        return len(messages)
    except Exception as e:
        log_error(message="Envoi de l'alerte APIs impossible", module="API", exception=e)
        return 0


def reinitialiser_etat():
    """Remet à zéro l'état mémoire (utile pour les tests)."""
    _echecs.clear()
    _en_panne_signalee.clear()
