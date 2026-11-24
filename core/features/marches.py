# core/features/marches.py
"""
Stubs pour les marchés spécialisés (corners, cartons, buteur, etc.).
Catégorie : marchés / prédiction
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #9 - Pronostics corners et cartons
# ---------------------------------------------------------------------------
def pronostics_corners_cartons(*args, **kwargs):
    """
    Marchés spécialisés en plus du 1N2.
    Dépendances externes : API stats corners/cartons.
    """
    log_warning("pronostics_corners_cartons appelé - stub à compléter", "FEATURES#9")
    return {
        "status": "a_implanter",
        "feature_id": 9,
        "libelle": "Pronostics corners et cartons",
        "message": "À implémenter : pronostics sur les marchés corners et cartons",
        "dependances": ["API stats corners/cartons"],
    }


# ---------------------------------------------------------------------------
# Feature #25 - Statistiques des arbitres
# ---------------------------------------------------------------------------
def stats_arbitres(*args, **kwargs):
    """
    Cartons moyens et données utiles pour les marchés cartons.
    Dépendances externes : API arbitres.
    """
    log_warning("stats_arbitres appelé - stub à compléter", "FEATURES#25")
    return {
        "status": "a_implanter",
        "feature_id": 25,
        "libelle": "Statistiques des arbitres",
        "message": "À implémenter : cartons moyens et données pour marchés cartons",
        "dependances": ["API arbitres"],
    }


# ---------------------------------------------------------------------------
# Feature #29 - Spécialiste du match nul
# ---------------------------------------------------------------------------
def specialiste_match_nul(*args, **kwargs):
    """
    Filtre les gros matchs nuls probables avec cote élevée.
    Dépendances externes : modèle IA match nul.
    """
    log_warning("specialiste_match_nul appelé - stub à compléter", "FEATURES#29")
    return {
        "status": "a_implanter",
        "feature_id": 29,
        "libelle": "Spécialiste du match nul",
        "message": "À implémenter : filtre des gros matchs nuls probables cote élevée",
        "dependances": ["modèle IA match nul"],
    }


# ---------------------------------------------------------------------------
# Feature #29 (bis) - Pronostics buteur et passeur
# ---------------------------------------------------------------------------
def pronostics_buteur_passeur(*args, **kwargs):
    """
    Probabilités individuelles pour les marchés buteur/passeur.
    Dépendances externes : API joueurs.
    """
    log_warning("pronostics_buteur_passeur appelé - stub à compléter", "FEATURES#29b")
    return {
        "status": "a_implanter",
        "feature_id": 29,
        "libelle": "Pronostics buteur et passeur",
        "message": "À implémenter : probabilités individuelles buteur/passeur",
        "dependances": ["API joueurs"],
    }
