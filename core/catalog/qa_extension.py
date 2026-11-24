"""Checks QA administrables pour les parcours principaux du bot."""

from core.catalog.fonctionnalites_700 import fraicheur_donnees


def verifier_schema_utilisateur(utilisateur):
    requis = {"user_id", "first_name", "status"}
    manquants = sorted(requis - set(utilisateur or {}))
    return {"valide": not manquants, "manquants": manquants}


def verifier_reponse_prediction(reponse):
    champs = {"p_h", "p_d", "p_a"}
    manquants = sorted(champs - set(reponse or {}))
    if manquants:
        return {"valide": False, "manquants": manquants}
    total = sum(float(reponse[nom]) for nom in ("p_h", "p_d", "p_a"))
    valide = abs(total - 1.0) <= 0.02
    return {"valide": valide, "somme": round(total, 6), "manquants": []}


def verifier_fraicheur_sources(dates, maximum_minutes=30):
    return fraicheur_donnees(dates, maximum_minutes=maximum_minutes)


def executer_checks_qa(utilisateur=None, prediction=None, sources=None):
    checks = {
        "utilisateur": verifier_schema_utilisateur(utilisateur or {}),
        "prediction": verifier_reponse_prediction(prediction or {}),
        "sources": verifier_fraicheur_sources(sources or []),
    }
    return {"valide": all(check["valide"] for check in checks.values()), "checks": checks}
