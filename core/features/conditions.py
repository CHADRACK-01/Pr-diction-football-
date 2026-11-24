# core/features/conditions.py
"""
Stubs pour les conditions (météo, pelouse, altitude, motivation).
Catégorie : conditions / données
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #35 - Alerte météo et pelouse
# ---------------------------------------------------------------------------
def alerte_meteo_pelouse(*args, **kwargs):
    """
    Analyse pluie, surface synthétique et autres conditions.
    Dépendances externes : API météo OpenWeather.
    """
    log_warning("alerte_meteo_pelouse appelé - stub à compléter", "FEATURES#35")
    return {
        "status": "a_implanter",
        "feature_id": 35,
        "libelle": "Alerte météo et pelouse",
        "message": "À implémenter : analyse météo et état de la pelouse",
        "dependances": ["API météo OpenWeather"],
    }


# ---------------------------------------------------------------------------
# Feature #57 - Effet altitude et voyage
# ---------------------------------------------------------------------------
def effet_altitude_voyage(*args, **kwargs):
    """
    Analyse les trajets, altitudes et effets de fatigue.
    Dépendances externes : données voyages.
    """
    log_warning("effet_altitude_voyage appelé - stub à compléter", "FEATURES#57")
    return {
        "status": "a_implanter",
        "feature_id": 57,
        "libelle": "Effet altitude et voyage",
        "message": "À implémenter : analyse trajets, altitude, fatigue",
        "dependances": ["données voyages"],
    }


# ---------------------------------------------------------------------------
# Feature #60 - Indice de motivation
# ---------------------------------------------------------------------------
def indice_motivation(*args, **kwargs):
    """
    Évalue les enjeux sportifs des équipes.
    Dépendances externes : enjeux sportifs.
    """
    log_warning("indice_motivation appelé - stub à compléter", "FEATURES#60")
    return {
        "status": "a_implanter",
        "feature_id": 60,
        "libelle": "Indice de motivation",
        "message": "À implémenter : évaluation des enjeux sportifs des équipes",
        "dependances": ["enjeux sportifs"],
    }
