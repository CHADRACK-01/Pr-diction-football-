# core/predictions/nouveau_prediction.py
"""
Moteur de prédiction V2.

- Traduction des noms d'équipes (Telegram -> Base de données)
- Reconstruit les features (Elo, forme, moyennes de buts)
- Calcule le H2H, les scores exacts (Poisson) et le Value Bet
- Expose la matrice de Poisson complète pour les Premiums (Fonctionnalité 414)

Toutes les fonctions publiques retournent des dictionnaires typés pour
compatible avec les handlers Telegram existants.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np

from core.predictions.ml_model import global_model_data
from users.database import db_fetchall

from core.utils.logs import log_info, log_error, log_warning
from core.betting.value_bet import analyser_value_bet
from core.predictions import poisson

TZ_KINSHASA = timezone(timedelta(hours=1))

_etat_lock = threading.Lock()


# =========================================================
# DICTIONNAIRE DE CORRESPONDANCE DES NOMS
# =========================================================
NOMS_EQUIPES_MAPPING: dict[str, str] = {
    # Allemagne
    "FC Bayern München": "Bayern Munich",
    "Bayern München": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Borussia Mönchengladbach": "M'gladbach",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "1. FC Union Berlin": "Union Berlin",
    "SC Freiburg": "Freiburg",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "FC Augsburg": "Augsburg",
    "1. FSV Mainz 05": "Mainz",
    "SV Werder Bremen": "Werder Bremen",
    "VfL Bochum 1848": "Bochum",
    "1. FC Köln": "FC Koln",
    "SV Darmstadt 98": "Darmstadt",
    "1. FC Heidenheim 1846": "Heidenheim",
    "FC St. Pauli": "St Pauli",
    "Holstein Kiel": "Holstein Kiel",
    # France
    "Paris Saint-Germain FC": "Paris SG",
    "Paris Saint-Germain": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon",
    "AS Monaco FC": "Monaco",
    "LOSC Lille": "Lille",
    "OGC Nice": "Nice",
    "Stade Rennais FC 1901": "Rennes",
    "Racing Club de Lens": "Lens",
    "Stade de Reims": "Reims",
    "Montpellier HSC": "Montpellier",
    "FC Nantes": "Nantes",
    "Stade Brestois 29": "Brest",
    "RC Strasbourg Alsace": "Strasbourg",
    "Toulouse FC": "Toulouse",
    "FC Metz": "Metz",
    "Le Havre AC": "Le Havre",
    "Clermont Foot 63": "Clermont",
    "FC Lorient": "Lorient",
    "Angers SCO": "Angers",
    "AS Saint-Etienne": "St Etienne",
    "AJ Auxerre": "Auxerre",
    # Espagne
    "Real Madrid CF": "Real Madrid",
    "FC Barcelona": "Barcelona",
    "Atletico de Madrid": "Ath Madrid",
    "Atlético Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao",
    "Real Sociedad de Futbol": "Sociedad",
    "Real Betis Balompie": "Betis",
    "Sevilla FC": "Sevilla",
    "Valencia CF": "Valencia",
    "Villarreal CF": "Villarreal",
    "Getafe CF": "Getafe",
    "RCD Espanyol de Barcelona": "Espanol",
    "Rayo Vallecano de Madrid": "Vallecano",
    "RC Celta de Vigo": "Celta",
    "RCD Mallorca": "Mallorca",
    "CA Osasuna": "Osasuna",
    "Granada CF": "Granada",
    "Deportivo Alaves": "Alaves",
    "Cadiz CF": "Cadiz",
    "UD Las Palmas": "Las Palmas",
    "Girona FC": "Girona",
    "Real Valladolid CF": "Valladolid",
    "Levante UD": "Levante",
    "Elche CF": "Elche",
    "CD Leganes": "Leganes",
    "Real Zaragoza": "Zaragoza",
    "Real Oviedo": "Oviedo",
    "Sporting Gijon": "Sp Gijon",
    # Angleterre
    "Manchester City FC": "Man City",
    "Manchester United FC": "Man United",
    "Newcastle United FC": "Newcastle",
    "Nottingham Forest FC": "Nott'm Forest",
    "Tottenham Hotspur FC": "Tottenham",
    "Wolverhampton Wanderers FC": "Wolves",
    "Brighton & Hove Albion FC": "Brighton",
    "West Ham United FC": "West Ham",
    # Italie
    "AS Roma": "Roma",
    "SS Lazio": "Lazio",
    "Juventus FC": "Juventus",
    "AC Milan": "Milan",
    "FC Internazionale Milano": "Inter",
    "SSC Napoli": "Napoli",
    "ACF Fiorentina": "Fiorentina",
    "Atalanta BC": "Atalanta",
    "Bologna FC 1909": "Bologna",
    "Torino FC": "Torino",
    "Udinese Calcio": "Udinese",
    "US Sassuolo Calcio": "Sassuolo",
    "Empoli FC": "Empoli",
    "US Lecce": "Lecce",
    "Hellas Verona FC": "Verona",
    "Cagliari Calcio": "Cagliari",
    "Genoa CFC": "Genoa",
    "US Salernitana 1919": "Salernitana",
    "Frosinone Calcio": "Frosinone",
    "AC Monza": "Monza",
    "Parma Calcio 1913": "Parma",
    "Como 1907": "Como",
    "Venezia FC": "Venezia",
}


# Convention du contrat (core/contrat_modele.py) :
# 0 = domicile, 1 = nul, 2 = extérieur
CLASSES_1N2_CONTRAT: dict[int | str, str] = {0: "H", 1: "D", 2: "A"}


# =========================================================
# FONCTIONS PRIVÉES — État et features
# =========================================================


def _etat_a_jour() -> Any | None:
    """Renvoie l'état des équipes, avancé avec les matchs postérieurs au modèle.

    Seuls les matchs de date strictement postérieure à la dernière date déjà
    intégrée dans l'état (etat.date_max) sont ajoutés : un match n'est jamais
    compté deux fois, même si la fonction est appelée plusieurs fois.

    Returns:
        L'objet EtatEquipes mis à jour, ou None si le modèle n'est pas chargé.
    """
    etat = global_model_data.get("etat")
    if etat is None:
        return None
    with _etat_lock:
        rows = db_fetchall(
            """
            SELECT date, home_team, away_team, fthg, ftag, ftr
            FROM matchs
            WHERE fthg IS NOT NULL AND ftag IS NOT NULL AND ftr IS NOT NULL
              AND date > ?
            ORDER BY date, id
            """,
            params=[etat.date_max or ""],
            db_context={"table": "matchs", "operation": "features_maj"},
        )
        for r in rows:
            etat.mettre_a_jour({
                "date": r[0], "home": r[1], "away": r[2],
                "fthg": r[3], "ftag": r[4], "ftr": r[5],
            })
    return etat


def _get_team_features(
    home_team: str,
    away_team: str,
    date: str | None = None,
) -> dict[str, float] | None:
    """Features du match, calculées exactement comme à l'entraînement.

    Renvoie None si l'historique d'une des équipes est insuffisant.

    Args:
        home_team: Nom de l'équipe à domicile (déjà mappé en base).
        away_team: Nom de l'équipe à l'extérieur (déjà mappé en base).
        date: Date du match (YYYY-MM-DD). Si None, utilise la date du jour.

    Returns:
        Dictionnaire des features, ou None si données insuffisantes.
    """
    etat = _etat_a_jour()
    if etat is None:
        return None
    from datetime import datetime, timezone, timedelta
    jour = date or datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    feats = etat.predire(home_team, away_team, jour)
    if feats is None:
        return None
    # Alias utilisés par le calcul Poisson (buts marqués / encaissés par équipe)
    feats["bm_h"] = feats["marques_h"]
    feats["be_h"] = feats["encaisses_h"]
    feats["bm_a"] = feats["marques_a"]
    feats["be_a"] = feats["encaisses_a"]
    return feats


def _get_h2h(home_team: str, away_team: str) -> dict[str, int] | None:
    """Récupère les 5 dernières confrontations directes.

    Returns:
        Dictionnaire avec victoires_h, nuls, victoires_a, total, ou None.
    """
    rows = db_fetchall(
        """
        SELECT home_team, away_team, fthg, ftag FROM matchs
        WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
        ORDER BY date DESC LIMIT 5
        """,
        params=[home_team, away_team, away_team, home_team],
    )
    if not rows:
        return None

    victoires_h, nuls, victoires_a = 0, 0, 0
    for r in rows:
        h, a, fthg, ftag = r[0], r[1], r[2], r[3]
        if h == home_team:
            if fthg > ftag:
                victoires_h += 1
            elif fthg == ftag:
                nuls += 1
            else:
                victoires_a += 1
        else:
            if ftag > fthg:
                victoires_h += 1
            elif ftag == fthg:
                nuls += 1
            else:
                victoires_a += 1

    return {
        "victoires_h": victoires_h,
        "nuls": nuls,
        "victoires_a": victoires_a,
        "total": len(rows),
    }


# =========================================================
# FONCTIONS PRIVÉES — Probabilités modèles
# =========================================================


def _probas_1n2(modele: Any, X: np.ndarray) -> tuple[float, float, float]:
    """Retourne (p_H, p_D, p_A) en respectant l'ordre réel des classes du modèle 1N2.

    Args:
        modele: Modèle entraîné avec predict_proba et attribut classes_.
        X: Vecteur de features (1 x n_features).

    Returns:
        Tuple (p_home, p_draw, p_away) dans [0, 1].
    """
    classes_brutes = list(getattr(modele, "classes_", []))
    classes = [CLASSES_1N2_CONTRAT.get(c, c) for c in classes_brutes]
    probas = modele.predict_proba(X)[0]
    mapping = dict(zip(classes, probas))
    if {"H", "D", "A"}.issubset(mapping.keys()):
        return float(mapping["H"]), float(mapping["D"]), float(mapping["A"])
    log_warning(
        f"Classes 1N2 inattendues : {classes_brutes} — repli sur l'ordre p[0], p[1], p[2]",
        "PREDICTION",
    )
    return float(probas[0]), float(probas[1]), float(probas[2])


def _proba_classe_positive(modele: Any, X: np.ndarray) -> float | None:
    """Retourne la probabilité de la classe positive d'un modèle binaire.

    Les valeurs reconnues comme positives : "1", "true", "yes", "oui", "y".
    Retourne None si aucune classe positive n'est identifiée (pas de repli
    silencieux sur l'ordre des probabilités).

    Args:
        modele: Modèle entraîné avec predict_proba et attribut classes_.
        X: Vecteur de features (1 x n_features).

    Returns:
        Probabilité de la classe positive, ou None.
    """
    classes = list(getattr(modele, "classes_", []))
    probas = modele.predict_proba(X)[0]
    mapping = dict(zip(classes, probas))
    for valeur in ("1", "true", "yes", "oui", "y"):
        for cle, proba in mapping.items():
            if str(cle).lower() == valeur:
                return float(proba)
    log_warning(
        "Aucune classe positive identifiée : repli silencieux désactivé",
        "PREDICTION",
        extra={"classes": classes},
    )
    return None


# =========================================================
# FONCTION PUBLIQUE — Prédiction principale
# =========================================================


def predire_match_v2(
    home_team: str,
    away_team: str,
    competition: str = "default",
    cotes_book: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Fonction principale de prédiction V2.

    Orchestre le calcul des probabilités 1N2, doubles chances, over/under,
    BTTS, H2H, scores exacts (Poisson) et value bet.

    Args:
        home_team: Nom de l'équipe à domicile.
        away_team: Nom de l'équipe à l'extérieur.
        competition: Nom de la compétition (défaut: "default").
        cotes_book: Cotes bookmaker par issue (ex: {"h": 2.1, "d": 3.4, "a": 3.8}).

    Returns:
        Dictionnaire contenant les probabilités et analyses. En cas d'erreur,
        contient la clé "erreur" avec un message lisible.
    """
    from config import SEUIL_DIVERGENCE_DC

    home_team_db = NOMS_EQUIPES_MAPPING.get(home_team, home_team)
    away_team_db = NOMS_EQUIPES_MAPPING.get(away_team, away_team)

    models = global_model_data.get("models")
    if not models:
        # Chargement à la demande : le modèle peut ne pas être prêt au premier message
        from core.predictions.ml_model import charger_et_entrainer

        charger_et_entrainer()
        models = global_model_data.get("models")
    if not models:
        return {"erreur": "Modèle IA non chargé. Réessaie dans un instant."}

    feats = _get_team_features(home_team_db, away_team_db)
    if not feats:
        return {"erreur": f"Pas assez d'historique pour {home_team} vs {away_team}."}

    feature_names = global_model_data.get("features", [])
    features_manquantes = [nom for nom in feature_names if nom not in feats]
    if features_manquantes:
        log_error(
            "Features manquantes pour la prédiction",
            "PREDICTION",
            extra={
                "home": home_team,
                "away": away_team,
                "features": features_manquantes,
            },
        )
        return {"erreur": f"Données incomplètes pour {home_team} vs {away_team}."}

    X = np.array([[feats[nom] for nom in feature_names]])

    try:
        result: dict[str, Any] = {
            "home_team": home_team,
            "away_team": away_team,
            "competition": competition,
        }

        # --- Probabilités 1N2 ---
        if "1N2" in models:
            result["p_h"], result["p_d"], result["p_a"] = _probas_1n2(models["1N2"], X)
        else:
            result["p_h"], result["p_d"], result["p_a"] = 0.33, 0.33, 0.33

        # --- Doubles chances (dérivées du 1N2, source unique) ---
        result["dc_1x"] = result["p_h"] + result["p_d"]
        result["dc_x2"] = result["p_d"] + result["p_a"]
        result["dc_12"] = result["p_h"] + result["p_a"]

        # --- Contrôle de divergence avec le modèle DC_1X (si présent) ---
        if "DC_1X" in models:
            dc_1x_modele = _proba_classe_positive(models["DC_1X"], X)
            if (
                dc_1x_modele is not None
                and abs(dc_1x_modele - result["dc_1x"]) > SEUIL_DIVERGENCE_DC
            ):
                log_warning(
                    "Divergence entre le 1N2 et le modèle DC_1X",
                    "PREDICTION",
                    extra={
                        "dc_1x_1n2": round(result["dc_1x"], 4),
                        "dc_1x_modele": round(dc_1x_modele, 4),
                        "seuil_divergence": SEUIL_DIVERGENCE_DC,
                    },
                )

        # --- Over 2.5 ---
        over_25 = (
            _proba_classe_positive(models["Over25"], X)
            if "Over25" in models
            else 0.5
        )
        if over_25 is None:
            log_warning(
                "Probabilité Over 2.5 indisponible, valeur par défaut 0.5 utilisée",
                "PREDICTION",
                extra={"modele": "Over25"},
            )
            over_25 = 0.5
        result["over_25"] = over_25

        # --- BTTS ---
        btts_yes = (
            _proba_classe_positive(models["BTTS"], X)
            if "BTTS" in models
            else 0.5
        )
        if btts_yes is None:
            log_warning(
                "Probabilité BTTS indisponible, valeur par défaut 0.5 utilisée",
                "PREDICTION",
                extra={"modele": "BTTS"},
            )
            btts_yes = 0.5
        result["btts_yes"] = btts_yes

        # --- H2H ---
        result["h2h"] = _get_h2h(home_team_db, away_team_db)

        # --- Scores exacts (loi de Poisson, module pur core/poisson.py) ---
        lambda_h, lambda_a = poisson.calculer_lambdas(
            feats["bm_h"], feats["bm_a"], feats["be_h"], feats["be_a"]
        )
        result["top_scores"] = [
            (i, j, round(proba * 100, 2))
            for i, j, proba in poisson.top_scores(lambda_h, lambda_a, top=3)
        ]

        # --- Transmettre les lambdas et moyennes (pour MT et matrice Poisson) ---
        result["bm_h"] = feats["bm_h"]
        result["bm_a"] = feats["bm_a"]
        result["be_h"] = feats["be_h"]
        result["be_a"] = feats["be_a"]
        result["lambda_h"] = lambda_h
        result["lambda_a"] = lambda_a

        # --- Value Bet (verdict unifié via core.betting.value_bet) ---
        result["analyse_pari"] = None
        if cotes_book:
            issues = [
                ("1 (Domicile)", result["p_h"], cotes_book.get("h")),
                ("N (Nul)", result["p_d"], cotes_book.get("d")),
                ("2 (Extérieur)", result["p_a"], cotes_book.get("a")),
            ]
            label, proba, cote_book = max(issues, key=lambda x: x[1])
            result["analyse_pari"] = analyser_value_bet(proba, cote_book, label)

        return result

    except Exception as e:
        log_error(
            "Erreur de prédiction",
            "PREDICTION",
            extra={"home": home_team, "away": away_team},
            exception=e,
        )
        return {"erreur": "Erreur de calcul. L'admin a été prévenu."}


# =========================================================
# FONCTIONNALITÉ 414 : MATRICE DE POISSON (Accès PRO)
# =========================================================


def get_matrice_poisson(
    home_team: str,
    away_team: str,
    max_buts: int | None = None,
) -> dict[str, Any] | None:
    """Calcule la matrice de Poisson complète pour un match.

    Retourne None si :
    - le modèle IA n'est pas chargé (refus de donner l'illusion d'une
      prédiction IA sans modèle) ;
    - l'historique est insuffisant.

    Args:
        home_team: Nom de l'équipe à domicile.
        away_team: Nom de l'équipe à l'extérieur.
        max_buts: Nombre maximal de buts considérés par équipe.

    Returns:
        Dictionnaire avec lambda_home, lambda_away, top_scores, proba_over_25,
        proba_btts. Ou None en cas d'indisponibilité.
    """
    from config import POISSON_MAX_BUTS

    if max_buts is None:
        max_buts = POISSON_MAX_BUTS

    # Garde : refuser si le modèle n'est pas chargé.
    if not global_model_data.get("models"):
        log_warning(
            "get_matrice_poisson appelée sans modèle chargé",
            "PREDICTION",
            extra={"home": home_team, "away": away_team},
        )
        return None

    home_team_db = NOMS_EQUIPES_MAPPING.get(home_team, home_team)
    away_team_db = NOMS_EQUIPES_MAPPING.get(away_team, away_team)

    feats = _get_team_features(home_team_db, away_team_db)
    if not feats:
        return None

    lambda_h, lambda_a = poisson.calculer_lambdas(
        feats["bm_h"], feats["bm_a"], feats["be_h"], feats["be_a"]
    )

    grille = poisson.matrice_scores(lambda_h, lambda_a, max_buts=max_buts)
    matrice = [
        {"score": f"{i}-{j}", "proba": round(proba * 100, 2)}
        for (i, j), proba in grille.items()
    ]
    matrice.sort(key=lambda x: x["proba"], reverse=True)

    return {
        "lambda_home": round(lambda_h, 2),
        "lambda_away": round(lambda_a, 2),
        "top_scores": matrice[:10],
        "proba_over_25": round(
            poisson.proba_over(lambda_h, lambda_a, max_buts=max_buts) * 100, 2
        ),
        "proba_btts": round(
            poisson.proba_btts(lambda_h, lambda_a, max_buts=max_buts) * 100, 2
        ),
    }
