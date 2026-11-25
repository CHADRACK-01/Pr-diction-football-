# core/betting/gestion_risques.py
"""
Gestion des risques et plan anti-perte (fonctionnalités 47, 48, 54).

- Plan anti-perte : bloque les gros combinés après une série de pertes.
- Filtre de réussite par ligue : compare les performances historiques.
- Checklist avant pari : vérification des points de vigilance.

Aucune dépendance externe : logique métier pure.
"""

from __future__ import annotations

from typing import Any

from core.utils.logs import log_info, log_warning


def plan_anti_perte(
    pertes_consecutives: int,
    est_combine: bool = False,
    mise_demandee: float = 0.0,
    mise_max_sure: float = 5000.0,
) -> dict[str, Any]:
    """Plan anti-perte : limite les risques après une série de pertes.

    Après 3 pertes consécutives, bloque les gros combinés et ne propose
    que des paris sûrs. Après 5 pertes, bloque tous les paris.

    Args:
        pertes_consecutives: Nombre de pertes consécutives.
        est_combine: Si le pari est un combiné.
        mise_demandee: Montant de la mise demandée.
        mise_max_sure: Mise maximale pour un pari "sûr" (défaut 5000).

    Returns:
        Dictionnaire {bloque, raison, conseil, mise_max_autorisee}.
    """
    if pertes_consecutives >= 5:
        return {
            "bloque": True,
            "raison": "Plan anti-perte : 5 pertes consécutives, tous les paris bloqués",
            "conseil": "Pause suggérée de 24h. Reprenez avec une mise réduite.",
            "mise_max_autorisee": 0.0,
        }

    if pertes_consecutives >= 3 and est_combine:
        return {
            "bloque": True,
            "raison": "Plan anti-perte : 3 pertes consécutives, combinés bloqués",
            "conseil": "Proposez un pari simple ou attendez une victoire.",
            "mise_max_autorisee": mise_max_sure,
        }

    if pertes_consecutives >= 3:
        return {
            "bloque": False,
            "raison": None,
            "conseil": "Pertes consécutives détectées : misez prudemment (max 2% de la bankroll).",
            "mise_max_autorisee": min(mise_demandee, mise_max_sure),
        }

    return {
        "bloque": False,
        "raison": None,
        "conseil": None,
        "mise_max_autorisee": mise_demandee,
    }


def filtre_reussite_par_ligue(
    performances_ligues: dict[str, dict[str, float]],
    ligue: str,
    seuil_min: float = 0.55,
) -> dict[str, Any]:
    """Filtre de réussite par ligue : compare les performances historiques.

    Args:
        performances_ligues: Dictionnaire {nom_ligue: {taux_reussite, nb_matchs, roi}}.
        ligue: Nom de la ligue à évaluer.
        seuil_min: Taux de réussite minimum pour autoriser (défaut 55%).

    Returns:
        Dictionnaire {autorisee, taux_reussite, nb_matchs, roi, raison}.
    """
    perf = performances_ligues.get(ligue)
    if not perf:
        return {
            "autorisee": False,
            "taux_reussite": None,
            "nb_matchs": 0,
            "roi": None,
            "reason": f"Aucune donnée historique pour la ligue '{ligue}'",
        }

    taux = perf.get("taux_reussite", 0.0)
    nb_matchs = perf.get("nb_matchs", 0)
    roi = perf.get("roi", 0.0)

    autorisee = taux >= seuil_min and nb_matchs >= 10

    return {
        "autorisee": autorisee,
        "taux_reussite": round(taux, 4),
        "nb_matchs": nb_matchs,
        "roi": round(roi, 4),
        "reason": None if autorisee else f"Taux de réussite {taux*100:.1f}% en dessous du seuil {seuil_min*100:.0f}%",
    }


def checklist_avant_pari(
    compo_verifiee: bool = False,
    meteo_verifiee: bool = False,
    mise_verifiee: bool = False,
    bankroll_suffisante: bool = False,
    news_equipe_verifiee: bool = False,
) -> dict[str, Any]:
    """Checklist avant de parier : vérification des points de vigilance.

    Args:
        compo_verifiee: Composition officielle vérifiée.
        meteo_verifiee: Conditions météo vérifiées.
        mise_verifiee: Mise dans les limites de la bankroll.
        bankroll_suffisante: Bankroll suffisante pour le pari.
        news_equipe_verifiee: Nouvelles de l'équipe (blessés, suspensions) vérifiées.

    Returns:
        Dictionnaire {complete, elements_manquants, conseil}.
    """
    elements = {
        "composition officielle": compo_verifiee,
        "météo / pelouse": meteo_verifiee,
        "mise dans les limites": mise_verifiee,
        "bankroll suffisante": bankroll_suffisante,
        "actualités de l'équipe": news_equipe_verifiee,
    }

    manquants = [nom for nom, ok in elements.items() if not ok]
    complete = len(manquants) == 0

    conseil = (
        "Tous les points sont vérifiés. Vous pouvez parier en toute connaissance de cause."
        if complete
        else f"Vérifiez avant de parier : {', '.join(manquants)}."
    )

    return {
        "complete": complete,
        "elements_verifies": elements,
        "elements_manquants": manquants,
        "conseil": conseil,
    }
