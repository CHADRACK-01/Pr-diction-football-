# core/features/export.py
"""
Stubs pour les exports utilisateurs et revenus.
Catégorie : export / administration
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #128 - Export utilisateurs CSV ou Excel
# ---------------------------------------------------------------------------
def export_utilisateurs_csv_excel(*args, **kwargs):
    """
    Téléchargement de la base pour analyses.
    Dépendances externes : aucune.
    """
    log_warning("export_utilisateurs_csv_excel appelé - stub à compléter", "FEATURES#128")
    return {
        "status": "a_implanter",
        "feature_id": 128,
        "libelle": "Export utilisateurs CSV ou Excel",
        "message": "À implémenter : export de la base utilisateurs",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #129 - Export des revenus pour la comptabilité
# ---------------------------------------------------------------------------
def export_revenus_compta(*args, **kwargs):
    """
    Fichier mensuel structuré.
    Dépendances externes : aucune.
    """
    log_warning("export_revenus_compta appelé - stub à compléter", "FEATURES#129")
    return {
        "status": "a_implanter",
        "feature_id": 129,
        "libelle": "Export des revenus pour la comptabilité",
        "message": "À implémenter : export mensuel des revenus",
        "dependances": [],
    }
