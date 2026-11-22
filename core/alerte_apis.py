# core/alerte_apis.py
"""
Alerte admin si une API de données ne répond plus (fonctionnalité 133).

- Vérifie chaque source via son tester_api()
- N'alerte qu'après SEUIL_ECHECS contrôles consécutifs en échec (évite les faux positifs)
- Une seule alerte par panne, puis un message de rétablissement
- L'état de chaque source est stocké en base (table parametres), donc il survit
  aux redémarrages : une panne déjà signalée n'est pas re-signalée au redémarrage.
"""

import json

from core.utils.logs import log_info, log_error

SEUIL_ECHECS = 2
_PREFIXE_CLE = "api_etat_"


def _testeurs_par_defaut():
    from core.api import api_football, bzzoiro, openligadb, thesportsdb, football_data
    return {
        "API-Football": api_football.tester_api,
        "Football-Data": football_data.tester_api,
        "Bzzoiro": bzzoiro.tester_api,
        "OpenLigaDB": openligadb.tester_api,
        "TheSportsDB": thesportsdb.tester_api,
    }


class EtatEnBase:
    """Stockage de l'état dans la table parametres (persistant)."""

    def lire(self, nom):
        from users.admin import get_parametre
        brut = get_parametre(_PREFIXE_CLE + nom, None)
        if not brut:
            return {"echecs": 0, "signale": False}
        try:
            etat = json.loads(brut)
            return {"echecs": int(etat.get("echecs", 0)), "signale": bool(etat.get("signale", False))}
        except (ValueError, TypeError, AttributeError):
            return {"echecs": 0, "signale": False}

    def ecrire(self, nom, etat):
        from users.admin import set_parametre
        set_parametre(_PREFIXE_CLE + nom, json.dumps(etat), f"État de l'alerte API {nom}")


class EtatEnMemoire:
    """Stockage temporaire, utilisé par les tests."""

    def __init__(self):
        self._donnees = {}

    def lire(self, nom):
        return dict(self._donnees.get(nom, {"echecs": 0, "signale": False}))

    def ecrire(self, nom, etat):
        self._donnees[nom] = dict(etat)


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


def traiter_resultats(resultats, etat=None):
    """Met à jour l'état de chaque source et retourne la liste des messages à envoyer."""
    if etat is None:
        etat = EtatEnBase()
    messages = []
    for nom, ok in resultats.items():
        courant = etat.lire(nom)
        if ok:
            if courant["signale"]:
                messages.append(f"✅ {nom} répond de nouveau.")
            etat.ecrire(nom, {"echecs": 0, "signale": False})
        else:
            echecs = courant["echecs"] + 1
            signale = courant["signale"]
            if echecs >= SEUIL_ECHECS and not signale:
                signale = True
                messages.append(f"🚨 {nom} ne répond plus ({echecs} contrôles en échec).")
            etat.ecrire(nom, {"echecs": echecs, "signale": signale})
    return messages


def verifier_et_alerter(envoyer, testeurs=None, etat=None):
    """Contrôle les APIs et appelle envoyer(texte) s'il y a un changement d'état.

    Retourne le nombre de messages envoyés. Ne lève jamais d'exception.
    """
    try:
        resultats = verifier_apis(testeurs)
        messages = traiter_resultats(resultats, etat)
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
