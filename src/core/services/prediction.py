# core/services/prediction.py
"""
Service de prédiction football.

Orchestre :
- core.predictions.nouveau_prediction.predire_match_v2 (modèle ML + Poisson)
- core.predictions.poisson (loi de Poisson pure)
- core.domaine.Prediction / Probabilites1N2 (structures métier typées)

Dépendance externe : aucune (le modèle ML est chargé depuis models_cache en base Turso).
Si le modèle n'est pas chargé, retourne une erreur claire plutôt qu'un pronostic faux.
"""

from __future__ import annotations

from typing import Any

from core.domaine import Match, Probabilites1N2, Prediction
from core.exceptions import ModeleIndisponibleError, PredictionError
from core.predictions.nouveau_prediction import predire_match_v2, get_matrice_poisson
from core.utils.logs import log_info, log_error


class ServicePrediction:
    """Service de prédiction de matchs de football."""

    def predire(
        self,
        home_team: str,
        away_team: str,
        competition: str = "default",
        cotes_book: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Calcule une prédiction complète pour un match.

        Args:
            home_team: Nom de l'équipe à domicile.
            away_team: Nom de l'équipe à l'extérieur.
            competition: Nom de la compétition.
            cotes_book: Cotes bookmaker par issue ({"h": 2.1, "d": 3.4, "a": 3.8}).

        Returns:
            Dictionnaire avec les probabilités 1N2, doubles chances, over/under,
            BTTS, scores exacts, value bet. En cas d'erreur, contient la clé "erreur".

        Raises:
            ModeleIndisponibleError: Si le modèle ML n'est pas chargé.
        """
        try:
            log_info(
                f"Prédiction demandée : {home_team} vs {away_team} ({competition})",
                "SERVICE_PREDICTION",
            )

            resultat = predire_match_v2(
                home_team=home_team,
                away_team=away_team,
                competition=competition,
                cotes_book=cotes_book,
            )

            if "erreur" in resultat:
                raise PredictionError(resultat["erreur"])

            # Validation des probabilités via le domaine
            try:
                probas = Probabilites1N2(
                    p_home=resultat["p_h"],
                    p_draw=resultat["p_d"],
                    p_away=resultat["p_a"],
                )
            except ValueError as e:
                raise PredictionError(f"Probabilités invalides : {e}")

            match = Match(
                home_team=home_team,
                away_team=away_team,
                competition=competition,
                cote_home=cotes_book.get("h") if cotes_book else None,
                cote_draw=cotes_book.get("d") if cotes_book else None,
                cote_away=cotes_book.get("a") if cotes_book else None,
            )

            prediction = Prediction(
                match=match,
                probabilites=probas,
                score_predit=resultat.get("top_scores", [("", "", 0)])[0][0]
                if resultat.get("top_scores")
                else None,
                source="modele_ia",
                valeur_attendue=resultat.get("analyse_pari", {}).get("ev")
                if resultat.get("analyse_pari")
                else None,
                is_value_bet=resultat.get("analyse_pari", {}).get("is_value", False)
                if resultat.get("analyse_pari")
                else False,
                cote_book=cotes_book.get("h") if cotes_book else None,
            )

            return {
                "home_team": home_team,
                "away_team": away_team,
                "competition": competition,
                "p_h": probas.p_home,
                "p_d": probas.p_draw,
                "p_a": probas.p_away,
                "favori": probas.favori,
                "confiance": probas.confiance,
                "dc_1x": resultat.get("dc_1x"),
                "dc_x2": resultat.get("dc_x2"),
                "dc_12": resultat.get("dc_12"),
                "over_25": resultat.get("over_25"),
                "btts_yes": resultat.get("btts_yes"),
                "h2h": resultat.get("h2h"),
                "top_scores": [
                    {"score": f"{i}-{j}", "proba_pct": round(proba * 100, 2)}
                    for i, j, proba in resultat.get("top_scores", [])
                ],
                "lambda_h": resultat.get("lambda_h"),
                "lambda_a": resultat.get("lambda_a"),
                "analyse_pari": resultat.get("analyse_pari"),
                "est_fiable": prediction.est_fiable(),
            }

        except ModeleIndisponibleError:
            raise
        except PredictionError:
            raise
        except Exception as e:
            log_error(
                "Erreur service prédiction",
                "SERVICE_PREDICTION",
                exception=e,
                extra={"home": home_team, "away": away_team, "competition": competition},
            )
            raise PredictionError(f"Erreur de calcul : {type(e).__name__}") from e

    def matrice_poisson(
        self,
        home_team: str,
        away_team: str,
        max_buts: int | None = None,
    ) -> dict[str, Any] | None:
        """Retourne la matrice de Poisson complète pour un match (Accès PRO).

        Retourne None si le modèle n'est pas chargé ou les données insuffisantes.
        """
        try:
            return get_matrice_poisson(home_team, away_team, max_buts)
        except Exception as e:
            log_error(
                "Erreur matrice Poisson",
                "SERVICE_PREDICTION",
                exception=e,
                extra={"home": home_team, "away": away_team},
            )
            return None
