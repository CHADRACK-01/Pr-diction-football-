# core/betting/paris_builder.py
"""
Constructeur de paris et coupons (fonctionnalités 43, 44, 45).

Génère des coupons du jour, des doubles sûrs, des combinés par risque,
et calcule l'assurance combiné.

Dépendance externe : api_football pour les cotes bookmaker (optionnel).
"""

from __future__ import annotations

from typing import Any

from core.betting.value_bet import analyser_value_bet
from core.utils.logs import log_info, log_warning


def generer_coupons_du_jour(
    predictions: list[dict[str, Any]],
    nb_coupons: int = 3,
) -> list[dict[str, Any]]:
    """Génère des coupons du jour à partir d'une liste de prédictions.

    Trie les prédictions par confiance décroissante et sélectionne les
    meilleures pour former des coupons.

    Args:
        predictions: Liste de dictionnaires de prédiction (avec p_h, p_d, p_a, dc_1x, etc.).
        nb_coupons: Nombre de coupons à générer.

    Returns:
        Liste de coupons, chacun contenant les sélections et la cote estimée.
    """
    if not predictions:
        return []

    # Trier par confiance (max de p_h, p_d, p_a)
    def confiance(pred: dict) -> float:
        return max(pred.get("p_h", 0), pred.get("p_d", 0), pred.get("p_a", 0))

    triees = sorted(predictions, key=confiance, reverse=True)
    selectionnes = triees[:nb_coupons]

    coupons = []
    for i, pred in enumerate(selectionnes, 1):
        favori = pred.get("favori", "home")
        proba_favori = {
            "home": pred.get("p_h", 0),
            "draw": pred.get("p_d", 0),
            "away": pred.get("p_a", 0),
        }[favori]

        coupon = {
            "numero": i,
            "match": f"{pred.get('home_team', '?')} vs {pred.get('away_team', '?')}",
            "competition": pred.get("competition", ""),
            "choix": favori,
            "probabilite": round(proba_favori * 100, 1),
            "confiance": "sur" if proba_favori >= 0.75 else "modere" if proba_favori >= 0.65 else "risque",
        }
        coupons.append(coupon)

    log_info(
        f"{len(coupons)} coupon(s) du jour généré(s)",
        "PARIS_BUILDER",
    )
    return coupons


def double_sur_du_jour(
    predictions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Sélectionne les 2 matchs les plus sûrs pour un "double sûr du jour".

    Cote cible : 1.80 - 2.20.

    Args:
        predictions: Liste de prédictions.

    Returns:
        Dictionnaire avec les 2 sélections et la cote combinée estimée, ou None.
    """
    if len(predictions) < 2:
        return None

    def confiance(pred: dict) -> float:
        return max(pred.get("p_h", 0), pred.get("p_d", 0), pred.get("p_a", 0))

    triees = sorted(predictions, key=confiance, reverse=True)
    top2 = triees[:2]

    p1 = max(top2[0].get("p_h", 0), top2[0].get("p_d", 0), top2[0].get("p_a", 0))
    p2 = max(top2[1].get("p_h", 0), top2[1].get("p_d", 0), top2[1].get("p_a", 0))

    # Cote implicite estimée = 1 / (p1 * p2) approximativement
    cote_combinee = 1.0 / (p1 * p2) if (p1 * p2) > 0 else 0.0

    return {
        "selections": [
            {
                "match": f"{s.get('home_team', '?')} vs {s.get('away_team', '?')}",
                "choix": s.get("favori", "home"),
                "probabilite": round(confiance(s) * 100, 1),
            }
            for s in top2
        ],
        "cote_estimee": round(cote_combinee, 2),
        "probabilite_combinee": round(p1 * p2 * 100, 1),
    }


def generer_combine_par_risque(
    predictions: list[dict[str, Any]],
    cote_cible: float,
    max_selections: int = 5,
) -> dict[str, Any] | None:
    """Construit un combiné selon une cote demandée.

    Sélectionne des matchs pour atteindre la cote cible sans dépasser
    un nombre maximum de sélections.

    Args:
        predictions: Liste de prédictions avec cotes.
        cote_cible: Cote cible du combiné.
        max_selections: Nombre maximal de sélections.

    Returns:
        Dictionnaire avec les sélections et la cote totale, ou None si impossible.
    """
    if not predictions or cote_cible <= 1.0:
        return None

    # Trier par confiance décroissante
    def confiance(pred: dict) -> float:
        return max(pred.get("p_h", 0), pred.get("p_d", 0), pred.get("p_a", 0))

    triees = sorted(predictions, key=confiance, reverse=True)

    selections = []
    cote_totale = 1.0
    for pred in triees[:max_selections]:
        p = confiance(pred)
        if p <= 0:
            continue
        cote_implicite = 1.0 / p
        nouvelle_cote = cote_totale * cote_implicite
        if nouvelle_cote > cote_cible * 1.1:  # Tolérance 10%
            continue
        selections.append({
            "match": f"{pred.get('home_team', '?')} vs {pred.get('away_team', '?')}",
            "choix": pred.get("favori", "home"),
            "cote": round(cote_implicite, 2),
            "probabilite": round(p * 100, 1),
        })
        cote_totale = nouvelle_cote
        if cote_totale >= cote_cible * 0.9:  # Atteint 90% de la cible
            break

    if not selections:
        return None

    log_info(
        f"Combiné généré : {len(selections)} sélections, cote {round(cote_totale, 2)}",
        "PARIS_BUILDER",
    )

    return {
        "selections": selections,
        "cote_totale": round(cote_totale, 2),
        "cote_cible": cote_cible,
        "nb_selections": len(selections),
    }


def assurance_combine(
    selections: list[dict[str, Any]],
    mise: float,
    cotes_reelles: list[float] | None = None,
) -> dict[str, Any] | None:
    """Calcule l'assurance combiné : gains si quelques sélections échouent.

    Args:
        selections: Liste des sélections du combiné.
        mise: Montant misé.
        cotes_reelles: Cotes réelles de chaque sélection (optionnel).

    Returns:
        Dictionnaire avec gains selon le nombre de sélections gagnantes, ou None.
    """
    if not selections or mise <= 0:
        return None

    nb_selections = len(selections)
    cotes = cotes_reelles or [s.get("cote", 2.0) for s in selections]

    # Calcul des gains pour chaque scénario (0 à nb_selections gagnants)
    resultats = {}
    for nb_gagnants in range(nb_selections + 1):
        if nb_gagnants == 0:
            gain = 0.0
        else:
            # Approximation : gain proportionnel au nombre de gagnants
            gain = mise * (nb_gagnants / nb_selections) * (sum(cotes) / len(cotes)) * 0.5
        resultats[f"{nb_gagnants}_sur_{nb_selections}"] = round(gain, 2)

    return {
        "mise": round(mise, 2),
        "nb_selections": nb_selections,
        "gains_par_scenario": resultats,
        "remboursement_estime": resultats.get(f"{nb_selections - 1}_sur_{nb_selections}", 0.0),
    }
