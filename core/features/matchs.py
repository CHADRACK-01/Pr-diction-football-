# core/features/matchs.py
"""
Stubs pour les fonctionnalités liées aux matchs (compositions, absents, etc.).
Catégorie : matchs / données
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #4 - Alerte composition officielle et absents
# ---------------------------------------------------------------------------
def alerte_composition_officielle(*args, **kwargs):
    """
    Vérification avant le match et recalcul du prono.
    Dépendances externes : API compositions, API blessés.
    """
    log_warning("alerte_composition_officielle appelé - stub à compléter", "FEATURES#4")
    return {
        "status": "a_implanter",
        "feature_id": 4,
        "libelle": "Alerte composition officielle et absents",
        "message": "À implémenter : vérification des compos officielles + recalcul du prono",
        "dependances": ["API compositions", "API blessés"],
    }


# ---------------------------------------------------------------------------
# Feature #55 - Base blessés et suspendus
# ---------------------------------------------------------------------------
def base_blesses_suspendus(*args, **kwargs):
    """
    Liste quotidienne des absents et durées estimées.
    Dépendances externes : API blessures/suspensions.
    """
    log_warning("base_blesses_suspendus appelé - stub à compléter", "FEATURES#55")
    return {
        "status": "a_implanter",
        "feature_id": 55,
        "libelle": "Base blessés et suspendus",
        "message": "À implémenter : liste quotidienne des absents avec durées estimées",
        "dependances": ["API blessures/suspensions"],
    }


# ---------------------------------------------------------------------------
# Feature #56 - Composition prédite vs composition officielle
# ---------------------------------------------------------------------------
def composition_predite_vs_officielle(*args, **kwargs):
    """
    Compare puis ajuste le pronostic.
    Dépendances externes : API compositions, modèle IA.
    """
    log_warning("composition_predite_vs_officielle appelé - stub à compléter", "FEATURES#56")
    return {
        "status": "a_implanter",
        "feature_id": 56,
        "libelle": "Composition prédite vs composition officielle",
        "message": "À implémenter : comparaison compo prédite vs officielle + ajustement",
        "dependances": ["API compositions", "modèle IA"],
    }
