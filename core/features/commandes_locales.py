# core/features/commandes_locales.py
"""
Stubs pour les commandes locales ajoutées (/daily, /roue, etc.).
Catégorie : commandes_locales
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #143 - Commande /daily - bonus de connexion quotidien
# ---------------------------------------------------------------------------
def cmd_daily(*args, **kwargs):
    """
    Récupérer le bonus de connexion quotidien.
    Dépendances externes : aucune.
    """
    log_warning("cmd_daily appelé - stub à compléter", "FEATURES#143")
    return {
        "status": "a_implanter",
        "feature_id": 143,
        "libelle": "Commande /daily - bonus de connexion quotidien",
        "message": "À implémenter : bonus de connexion quotidien",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #144 - Commande /roue - roue quotidienne gratuite
# ---------------------------------------------------------------------------
def cmd_roue(*args, **kwargs):
    """
    Utiliser la roue quotidienne gratuite.
    Dépendances externes : aucune.
    """
    log_warning("cmd_roue appelé - stub à compléter", "FEATURES#144")
    return {
        "status": "a_implanter",
        "feature_id": 144,
        "libelle": "Commande /roue - roue quotidienne gratuite",
        "message": "À implémenter : roue quotidienne gratuite",
        "dependances": [],
    }
