# core/features/rapports.py
"""
Stubs pour les rapports (PDF mensuel, email hebdo).
Catégorie : rapports / utilisateur
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #79 - Rapport mensuel PDF
# ---------------------------------------------------------------------------
def rapport_mensuel_pdf(*args, **kwargs):
    """
    Synthèse réussite, rendement et gains du mois.
    Dépendances externes : générateur PDF.
    """
    log_warning("rapport_mensuel_pdf appelé - stub à compléter", "FEATURES#79")
    return {
        "status": "a_implanter",
        "feature_id": 79,
        "libelle": "Rapport mensuel PDF",
        "message": "À implémenter : synthèse mensuelle réussite/rendement/gains",
        "dependances": ["générateur PDF"],
    }


# ---------------------------------------------------------------------------
# Feature #80 - Résumé email hebdomadaire
# ---------------------------------------------------------------------------
def resume_email_hebdomadaire(*args, **kwargs):
    """
    Envoie les statistiques chaque dimanche.
    Dépendances externes : service email.
    """
    log_warning("resume_email_hebdomadaire appelé - stub à compléter", "FEATURES#80")
    return {
        "status": "a_implanter",
        "feature_id": 80,
        "libelle": "Résumé email hebdomadaire",
        "message": "À implémenter : envoi des statistiques chaque dimanche",
        "dependances": ["service email"],
    }
