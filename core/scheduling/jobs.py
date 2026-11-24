"""Tâches exécutables par le scheduler applicatif."""

from core.utils.logs import log_error, log_info


def mettre_a_jour_resultats():
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats as mettre_a_jour
        total = mettre_a_jour()
        log_info(f"Résultats mis à jour : {total} matchs.", "SCHEDULER")
        return total
    except Exception as e:
        log_error("Erreur maj résultats", "SCHEDULER", exception=e)
        return 0


def telecharger_matchs():
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        log_info(f"Matchs téléchargés : {total}.", "SCHEDULER")
        return total
    except Exception as e:
        log_error("Erreur téléchargement matchs", "SCHEDULER", exception=e)
        return 0


def nettoyer_matchs_anciens():
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        log_info(f"Matchs de plus de 5 ans supprimés : {total}.", "SCHEDULER")
        return total
    except Exception as e:
        log_error("Erreur nettoyage vieilles données", "SCHEDULER", exception=e)
        return 0
