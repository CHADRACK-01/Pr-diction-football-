# core/administration/dashboard_admin.py
"""
Dashboard administrateur temps réel.

Agrège les données : utilisateurs, pronostics, paiements, alertes, santé des APIs.
"""

from __future__ import annotations

from typing import Any


def dashboard_admin_temps_reel() -> dict[str, Any]:
    """Retourne un aperçu du état actuel du bot pour l'admin.

    Returns:
        Dictionnaire avec utilisateurs, pronostics_du_jour, paiements_en_attente,
        alertes_actives, sante_apis.
    """
    return {
        "utilisateurs": {"total": 0, "premium": 0, "gratuit": 0, "bannis": 0},
        "pronostics_du_jour": {"total": 0, "gagnants": 0, "perdants": 0},
        "paiements_en_attente": 0,
        "alertes_actives": [],
        "sante_apis": {"api_football": "inconnu", "paiements": "inconnu"},
        "note": "Implémentation de base - à connecter aux tables réelles via users/",
    }
