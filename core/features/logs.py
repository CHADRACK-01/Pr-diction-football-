# core/features/logs.py
"""
Stubs pour les logs, alertes API et contrôle d'erreurs.
Catégorie : logs / administration
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #132 - Logs d'erreurs lisibles
# ---------------------------------------------------------------------------
def logs_erreurs_lisibles(*args, **kwargs):
    """
    Affiche les pannes et événements de manière compréhensible.
    Dépendances externes : aucune.
    """
    log_warning("logs_erreurs_lisibles appelé - stub à compléter", "FEATURES#132")
    return {
        "status": "a_implanter",
        "feature_id": 132,
        "libelle": "Logs d'erreurs lisibles",
        "message": "À implémenter : affichage lisible des pannes et événements",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #133 - Alerte administrateur pour API morte
# ---------------------------------------------------------------------------
def alerte_api_morte_admin(*args, **kwargs):
    """
    Indique la source indisponible et la bascule possible.
    Dépendances externes : API externes.
    """
    log_warning("alerte_api_morte_admin appelé - stub à compléter", "FEATURES#133")
    return {
        "status": "a_implanter",
        "feature_id": 133,
        "libelle": "Alerte administrateur pour API morte",
        "message": "À implémenter : alerte si une API externe est indisponible",
        "dependances": ["API externes"],
    }


# ---------------------------------------------------------------------------
# Feature #134 - Alerte pic d'erreurs
# ---------------------------------------------------------------------------
def alerte_pic_erreurs(*args, **kwargs):
    """
    Avertit lorsqu'un seuil d'erreurs est dépassé.
    Dépendances externes : aucune.
    """
    log_warning("alerte_pic_erreurs appelé - stub à compléter", "FEATURES#134")
    return {
        "status": "a_implanter",
        "feature_id": 134,
        "libelle": "Alerte pic d'erreurs",
        "message": "À implémenter : avertissement si seuil d'erreurs dépassé",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #135 - Contrôle de consommation API
# ---------------------------------------------------------------------------
def controle_consommation_api(*args, **kwargs):
    """
    Affiche les appels utilisés et la limite disponible.
    Dépendances externes : API externes.
    """
    log_warning("controle_consommation_api appelé - stub à compléter", "FEATURES#135")
    return {
        "status": "a_implanter",
        "feature_id": 135,
        "libelle": "Contrôle de consommation API",
        "message": "À implémenter : suivi des appels API et limites",
        "dependances": ["API externes"],
    }


# ---------------------------------------------------------------------------
# Feature #136 - Gestion des sources prioritaires
# ---------------------------------------------------------------------------
def gestion_sources_prioritaires(*args, **kwargs):
    """
    Ordonne les API selon leur priorité.
    Dépendances externes : API externes.
    """
    log_warning("gestion_sources_prioritaires appelé - stub à compléter", "FEATURES#136")
    return {
        "status": "a_implanter",
        "feature_id": 136,
        "libelle": "Gestion des sources prioritaires",
        "message": "À implémenter : ordonnancement des API par priorité",
        "dependances": ["API externes"],
    }
