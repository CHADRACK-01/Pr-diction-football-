# core/features/ticket.py
"""
Stubs pour les tickets PDF, copie et export.
Catégorie : ticket / contenu
"""

from core.utils.logs import log_info, log_warning

# ---------------------------------------------------------------------------
# Feature #11 - Ticket de la semaine en PDF
# ---------------------------------------------------------------------------
def ticket_pdf_semaine(*args, **kwargs):
    """
    Image ou document partageable sur WhatsApp.
    Dépendances externes : générateur PDF.
    """
    log_warning("ticket_pdf_semaine appelé - stub à compléter", "FEATURES#11")
    return {
        "status": "a_implanter",
        "feature_id": 11,
        "libelle": "Ticket de la semaine en PDF",
        "message": "À implémenter : génération de ticket PDF partageable",
        "dependances": ["générateur PDF"],
    }


# ---------------------------------------------------------------------------
# Feature #19 - Copie du ticket en un clic
# ---------------------------------------------------------------------------
def copie_ticket_un_clic(*args, **kwargs):
    """
    Code directement utilisable chez les bookmakers.
    Dépendances externes : aucune.
    """
    log_warning("copie_ticket_un_clic appelé - stub à compléter", "FEATURES#19")
    return {
        "status": "a_implanter",
        "feature_id": 19,
        "libelle": "Copie du ticket en un clic",
        "message": "À implémenter : copie du code utilisable chez les bookmakers",
        "dependances": [],
    }


# ---------------------------------------------------------------------------
# Feature #40 - Export TikTok ou statut
# ---------------------------------------------------------------------------
def export_tiktok_statut(*args, **kwargs):
    """
    Image carrée avec logo et ticket du jour.
    Dépendances externes : générateur d'image.
    """
    log_warning("export_tiktok_statut appelé - stub à compléter", "FEATURES#40")
    return {
        "status": "a_implanter",
        "feature_id": 40,
        "libelle": "Export TikTok ou statut",
        "message": "À implémenter : image carrée avec logo et ticket du jour",
        "dependances": ["générateur d'image"],
    }
