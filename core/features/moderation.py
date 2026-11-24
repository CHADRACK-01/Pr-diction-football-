# core/features/moderation.py
"""
Stubs pour la modération et l'anti-spam.
Catégorie : modération
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #112 - Modération des mots interdits
# ---------------------------------------------------------------------------
def moderation_mots_interdits(*args, **kwargs):
    """
    Suppression des liens, insultes et numéros interdits.
    Dépendances externes : aucune.
    """
    log_warning("moderation_mots_interdits appelé - stub à compléter", "FEATURES#112")
    return {
        "status": "a_implanter",
        "feature_id": 112,
        "libelle": "Modération des mots interdits",
        "message": "À implémenter : suppression liens, insultes, numéros interdits",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #113 - Anti-spam automatique
# ---------------------------------------------------------------------------
def anti_spam_automatique(*args, **kwargs):
    """
    Mute temporaire après un nombre excessif de messages.
    Dépendances externes : aucune.
    """
    log_warning("anti_spam_automatique appelé - stub à compléter", "FEATURES#113")
    return {
        "status": "a_implanter",
        "feature_id": 113,
        "libelle": "Anti-spam automatique",
        "message": "À implémenter : mute temporaire après excès de messages",
        "dependances": [],
    }
