# core/features/langue.py
"""
Mode multilingue (implémentation réelle).
"""

from core.utils.logs import log_info, log_warning
from core.features.impl_reelles import mode_lingala_francais as _reel_lingala, mode_swahili as _reel_swahili

# ---------------------------------------------------------------------------
# Feature #6 - Mode Lingala et français
# ---------------------------------------------------------------------------
def mode_lingala_francais(*args, **kwargs):
    return _reel_lingala(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #82 - Mode Swahili
# ---------------------------------------------------------------------------
def mode_swahili(*args, **kwargs):
    return _reel_swahili(*args, **kwargs)


# ---------------------------------------------------------------------------
# Feature #83 - Commande vocale (stub - dépendance STT externe)
# ---------------------------------------------------------------------------
def commande_vocale(*args, **kwargs):
    log_warning("commande_vocale appelé - dépendance externe STT requise", "FEATURES#83")
    return {
        "status": "a_implanter",
        "feature_id": 83,
        "libelle": "Commande vocale",
        "message": "À implémenter : reconnaissance vocale (STT externe)",
        "dependances": ["reconnaissance vocale (STT)"],
    }


# ---------------------------------------------------------------------------
# Feature #84 - Recherche par emoji (réelle - pas de dépendance externe)
# ---------------------------------------------------------------------------
def recherche_par_emoji(requete: str) -> dict:
    """
    Extrait le nom d'équipe d'une requête contenant des emojis.
    Aucune dépendance externe.
    """
    import re
    # Supprime les emojis (plages Unicode)
    texte_net = re.sub(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u27BF]",
        " ",
        requete,
    )
    equipes = [m.strip() for m in texte_net.split() if m.strip() and not m.startswith("@")]
    return {
        "status": "complete",
        "feature_id": 84,
        "requete_originale": requete,
        "equipes_detectees": equipes,
        "message": f"Équipes détectées : {', '.join(equipes) if equipes else 'aucune'}",
        "dependances": [],
    }

