# core/features/audio.py
"""
Stubs pour les résumés vocaux et commentaires audio.
Catégorie : audio / contenu
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #37 - Résumé vocal
# ---------------------------------------------------------------------------
def resume_vocal(*args, **kwargs):
    """
    Audio de courte durée présentant les matchs du soir.
    Dépendances externes : TTS.
    """
    log_warning("resume_vocal appelé - stub à compléter", "FEATURES#37")
    return {
        "status": "a_implanter",
        "feature_id": 37,
        "libelle": "Résumé vocal",
        "message": "À implémenter : audio courte durée des matchs du soir",
        "dependances": ["TTS"],
    }


# ---------------------------------------------------------------------------
# Feature #51 - Résumé vocal IA de 30 secondes
# ---------------------------------------------------------------------------
def resume_vocal_ia_30s(*args, **kwargs):
    """
    Synthèse audio des trois matchs principaux.
    Dépendances externes : TTS, IA texte.
    """
    log_warning("resume_vocal_ia_30s appelé - stub à compléter", "FEATURES#51")
    return {
        "status": "a_implanter",
        "feature_id": 51,
        "libelle": "Résumé vocal IA de 30 secondes",
        "message": "À implémenter : synthèse audio des 3 matchs principaux",
        "dependances": ["TTS", "IA texte"],
    }
