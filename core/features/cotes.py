# core/features/cotes.py
"""
Stubs pour les fonctionnalités liées aux cotes et value bet.
Catégorie : cotes / paris
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #2 - Détecteur de value bet
# ---------------------------------------------------------------------------
def detecteur_value_bet(*args, **kwargs):
    """
    Compare la probabilité IA à la cote du bookmaker.
    Dépendances externes : API cotes bookmakers.
    """
    log_warning("detecteur_value_bet appelé - stub à compléter", "FEATURES#2")
    return {
        "status": "a_implanter",
        "feature_id": 2,
        "libelle": "Détecteur de value bet",
        "message": "À implémenter : comparaison probabilité IA vs cote bookmaker",
        "dependances": ["API cotes bookmakers"],
    }


# ---------------------------------------------------------------------------
# Feature #3 - Tracker de chute de cotes
# ---------------------------------------------------------------------------
def tracker_chute_cotes(*args, **kwargs):
    """
    Alerte lorsqu'une cote baisse rapidement.
    Dépendances externes : API cotes en temps réel.
    """
    log_warning("tracker_chute_cotes appelé - stub à compléter", "FEATURES#3")
    return {
        "status": "a_implanter",
        "feature_id": 3,
        "libelle": "Tracker de chute de cotes",
        "message": "À implémenter : détection des baisses rapides de cotes",
        "dependances": ["API cotes en temps réel"],
    }


# ---------------------------------------------------------------------------
# Feature #87 - Graphique d'évolution des cotes
# ---------------------------------------------------------------------------
def graphique_cotes(*args, **kwargs):
    """
    Courbe historique des cotes sur 24 heures ou plus.
    Dépendances externes : API cotes historiques.
    """
    log_warning("graphique_cotes appelé - stub à compléter", "FEATURES#87")
    return {
        "status": "a_implanter",
        "feature_id": 87,
        "libelle": "Graphique d'évolution des cotes",
        "message": "À implémenter : courbe historique des cotes sur 24h+",
        "dependances": ["API cotes historiques"],
    }


# ---------------------------------------------------------------------------
# Feature #39 - Alerte underdog
# ---------------------------------------------------------------------------
def alerte_underdog(*args, **kwargs):
    """
    Met en évidence les petites équipes avec une cote attractive.
    Dépendances externes : API cotes.
    """
    log_warning("alerte_underdog appelé - stub à compléter", "FEATURES#39")
    return {
        "status": "a_implanter",
        "feature_id": 39,
        "libelle": "Alerte underdog",
        "message": "À implémenter : mise en avant des équipes outsiders avec cotes attractives",
        "dependances": ["API cotes"],
    }
