# core/features/coach.py
"""
Stubs pour le coach IA en chat libre.
Catégorie : coach / prédiction
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #21 - Coach IA en chat libre
# ---------------------------------------------------------------------------
def coach_ia_chat_libre(*args, **kwargs):
    """
    Réponses analytiques aux questions sur un match.
    Dépendances externes : IA conversationnelle (Groq/Google AI).
    """
    log_warning("coach_ia_chat_libre appelé - stub à compléter", "FEATURES#21")
    return {
        "status": "a_implanter",
        "feature_id": 21,
        "libelle": "Coach IA en chat libre",
        "message": "À implémenter : réponses analytiques aux questions sur un match",
        "dependances": ["IA conversationnelle (Groq/Google AI)"],
    }
