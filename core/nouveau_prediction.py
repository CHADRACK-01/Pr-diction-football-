# core/nouveau_prediction.py
"""
Moteur de prédiction V2 (5 modèles LightGBM).
⚠️ CORRECTIONS :
- ht_home_sc et ht_away_sc sont maintenant DISTINCTS (features séparées)
- Vérification complète des champs avant construction du vecteur
- Dates de match parsées pour éviter les fuites (match futur uniquement)
"""

import numpy as np
import difflib

from core.ml_model import global_model_data, CACHE_MODELES
from users.db import db_fetchone, db_fetchall
from core.utils.logs import log_info, log_error, log_warning


# Champs obligatoires dans un dict de features
_CHAMPS_FEATURES_OBLIGATOIRES = [
    "ft_glob_sc", "ft_glob_co", "ht_glob_sc", "ht_glob_co",
    "ft_home_sc", "ft_away_sc",
    "ht_home_sc", "ht_away_sc",
    "ft_form", "ht_form",
]


def _charger_modeles():
    """Charge les modèles si nécessaire."""
    if global_model_data.get("modeles_par_competition"):
        return global_model_data["modeles_par_competition"]

    log_info("Modèles absents, chargement depuis Turso...", "PREDICTION")
    from core.ml_model import charger_et_entrainer
    if charger_et_entrainer():
        return global_model_data.get("modeles_par_competition")
    return None


def _trouver_nom_exact(nom_recherche, competition):
    """Cherche le nom d'équipe le plus proche (casse/typo)."""
    if not nom_recherche:
        return None

    rows = db_fetchall(
        """
        SELECT DISTINCT home_team FROM matchs_features WHERE competition = ?
        UNION
        SELECT DISTINCT away_team FROM matchs_features WHERE competition = ?
        """,
        params=[competition, competition],
        db_context={"table": "matchs_features", "operation": "find_team"},
    )
    equipes = [r[0] for r in rows] if rows else []

    if not equipes:
        log_warning(
            message=f"Aucune équipe en base pour '{competition}'",
            module="PREDICTION",
            extra={"competition": competition, "equipe": nom_recherche},
        )
        return nom_recherche

    # 1. Exact (insensible casse)
    for equipe in equipes:
        if equipe.lower() == nom_recherche.lower():
            return equipe

    # 2. Approximatif
    equipes_lower = {e.lower(): e for e in equipes}
    matches = difflib.get_close_matches(
        nom_recherche.lower(), list(equipes_lower.keys()), n=1, cutoff=0.6
    )
    if matches:
        return equipes_lower[matches[0]]

    return nom_recherche


def _get_team_stats(competition, team, n=5):
    """
    Récupère les stats des N derniers matchs d'une équipe.
    Retourne un dict ou None si aucune donnée.
    """
    rows = db_fetchall(
        """
        SELECT fthg, ftag, ftr, hthg, htag, htr, home_team, away_team, date
        FROM matchs_features
        WHERE competition = ? AND (home_team = ? OR away_team = ?)
        ORDER BY date DESC LIMIT ?
        """,
        params=[competition, team, team, n],
        db_context={
            "table": "matchs_features",
            "operation": "team_stats",
            "params": {"competition": competition, "team": team},
        },
    )

    if not rows:
        log_warning(
            message=f"Aucun historique pour '{team}' en '{competition}'",
            module="PREDICTION",
            extra={"competition": competition, "team": team},
        )
        return None

    ft_scored, ft_conceded = [], []
    ht_scored, ht_conceded = [], []
    ft_results, ht_results = [], []
    ft_home_scored, ft_away_scored = [], []

    # ⚠️ CORRECTION : séparation explicite home/away pour les features HT
    ht_home_scored, ht_away_scored = [], []

    for r in rows:
        fthg, ftag, ftr, hthg, htag, htr, home, away, date = r
        is_home = home == team

        # Sécurité : scores manquants
        fthg = fthg if fthg is not None else 0
        ftag = ftag if ftag is not None else 0
        hthg = hthg if hthg is not None else 0
        htag = htag if htag is not None else 0

        if is_home:
            ft_scored.append(fthg)
            ft_conceded.append(ftag)
            ht_scored.append(hthg)
            ht_conceded.append(htag)
            ht_home_scored.append(hthg)  # HT à domicile
            ft_home_scored.append(fthg)
        else:
            ft_scored.append(ftag)
            ft_conceded.append(fthg)
            ht_scored.append(htag)
            ht_conceded.append(hthg)
            ht_away_scored.append(htag)  # HT à l'extérieur
            ft_away_scored.append(ftag)

        # Résultat (1= victoire, 0.5= nul, 0= défaite)
        if ftr == "H":
            ft_results.append(1.0 if is_home else 0.0)
        elif ftr == "A":
            ft_results.append(1.0 if not is_home else 0.0)
        else:
            ft_results.append(0.5)

        if htr in ("H", "D", "A", "N"):
            if htr == "H":
                ht_results.append(1.0 if is_home else 0.0)
            elif htr == "A":
                ht_results.append(1.0 if not is_home else 0.0)
            else:
                ht_results.append(0.5)

    def wf(res):
        """Forme pondérée sur les 3 derniers matchs (3,2,1)."""
        if not res:
            return 0.5
        r = res[:3]
        w = [3, 2, 1][: len(r)]
        return sum(x * y for x, y in zip(w, r)) / sum(w)

    def avg(lst, default=1.0):
        return float(np.mean(lst)) if lst else default

    return {
        "ft_glob_sc": avg(ft_scored, 1.2),
        "ft_glob_co": avg(ft_conceded, 1.0),
        "ht_glob_sc": avg(ht_scored, 0.5),
        "ht_glob_co": avg(ht_conceded, 0.5),
        "ft_home_sc": avg(ft_home_scored, 1.3),
        "ft_away_sc": avg(ft_away_scored, 1.0),
        # ⚠️ CORRECTION : valeurs distinctes
        "ht_home_sc": avg(ht_home_scored, 0.5),
        "ht_away_sc": avg(ht_away_scored, 0.5),
        "ft_form": wf(ft_results),
        "ht_form": wf(ht_results),
    }


def _get_elo(competition, team):
    """Récupère l'Elo actuel d'une équipe."""
    row = db_fetchone(
        """
        SELECT h_elo_ft, a_elo_ft, home_team FROM matchs_features
        WHERE competition = ? AND (home_team = ? OR away_team = ?)
        ORDER BY date DESC LIMIT 1
        """,
        params=[competition, team, team],
        db_context={
            "table": "matchs_features",
            "operation": "elo",
            "params": {"competition": competition, "team": team},
        },
    )
    if not row:
        return 1500.0
    h_elo, a_elo, home = row
    if home == team:
        return h_elo if h_elo is not None else 1500.0
    return a_elo if a_elo is not None else 1500.0


def _verifier_features(features, equipe):
    """Vérifie que tous les champs obligatoires sont présents."""
    if not features:
        return False
    manquants = [c for c in _CHAMPS_FEATURES_OBLIGATOIRES if c not in features]
    if manquants:
        log_error(
            message=f"Features incomplètes pour '{equipe}'",
            module="PREDICTION",
            extra={"equipe": equipe, "manquants": manquants},
        )
        return False
    return True


def predire_match_v2(home_team, away_team, competition, cotes_book=None):
    """
    Fait une prédiction avec les 5 modèles LightGBM.
    Retourne un dict complet ou {"erreur": "..."}.
    """
    modeles = _charger_modeles()
    if not modeles:
        return {"erreur": "Modèle non chargé."}

    if competition not in modeles:
        log_error(
            message=f"Compétition '{competition}' non supportée par le modèle",
            module="PREDICTION",
            extra={"competition": competition},
        )
        return {"erreur": f"⚠️ Compétition '{competition}' non supportée."}

    # Résolution des noms
    home_reel = _trouver_nom_exact(home_team, competition)
    away_reel = _trouver_nom_exact(away_team, competition)

    if home_reel != home_team:
        log_info(
            f"Nom corrigé : '{home_team}' -> '{home_reel}'",
            "PREDICTION",
            extra={"competition": competition},
        )
    if away_reel != away_team:
        log_info(
            f"Nom corrigé : '{away_team}' -> '{away_reel}'",
            "PREDICTION",
            extra={"competition": competition},
        )

    h_feat = _get_team_stats(competition, home_reel)
    a_feat = _get_team_stats(competition, away_reel)

    if not h_feat or not a_feat:
        return {"erreur": f"⚠️ Données insuffisantes pour {home_team} ou {away_team}."}

    if not _verifier_features(h_feat, home_reel):
        return {"erreur": f"⚠️ Features incomplètes pour {home_reel}."}
    if not _verifier_features(a_feat, away_reel):
        return {"erreur": f"⚠️ Features incomplètes pour {away_reel}."}

    h_elo = _get_elo(competition, home_reel)
    a_elo = _get_elo(competition, away_reel)

    # Probabilités bookmaker (normalisées)
    p_h, p_d, p_a = 1 / 3, 1 / 3, 1 / 3
    if cotes_book and all(cotes_book.get(k) for k in ("h", "d", "a")):
        try:
            s = sum(1 / cotes_book[k] for k in ("h", "d", "a"))
            p_h = (1 / cotes_book["h"]) / s
            p_d = (1 / cotes_book["d"]) / s
            p_a = (1 / cotes_book["a"]) / s
        except ZeroDivisionError as e:
            log_error(
                message="Cotes bookmaker invalides (division par zéro)",
                module="PREDICTION",
                extra={"cotes_book": cotes_book},
                exception=e,
            )

    ft_f = np.array([[
        h_elo, a_elo, h_elo - a_elo,
        h_feat["ft_glob_sc"], h_feat["ft_glob_co"],
        a_feat["ft_glob_sc"], a_feat["ft_glob_co"],
        h_feat["ft_home_sc"], a_feat["ft_away_sc"],
        h_feat["ft_form"], a_feat["ft_form"],
        p_h, p_d, p_a,
    ]])

    ht_f = np.array([[
        h_elo, a_elo, h_elo - a_elo,
        h_feat["ht_glob_sc"], h_feat["ht_glob_co"],
        a_feat["ht_glob_sc"], a_feat["ht_glob_co"],
        h_feat["ht_home_sc"], a_feat["ht_away_sc"],  # ⚠️ CORRIGÉ
        h_feat["ht_form"], a_feat["ht_form"],
        p_h, p_d, p_a,
    ]])

    preds = {}
    for nom, info in modeles[competition].items():
        try:
            # Choisir le bon vecteur selon les features attendues
            is_ft = any("ft" in str(f) for f in info.get("features", []))
            X = ft_f if is_ft else ht_f
            X_scaled = info["scaler"].transform(X)
            proba = info["model"].predict_proba(X_scaled)[0]
            preds[nom] = proba
        except Exception as e:
            log_error(
                message=f"Erreur de prédiction pour le marché '{nom}'",
                module="PREDICTION",
                extra={
                    "competition": competition,
                    "marche": nom,
                    "home": home_reel,
                    "away": away_reel,
                },
                exception=e,
            )
            preds[nom] = None

    # Construction du résultat
    def safe_pred(nom, index):
        p = preds.get(nom)
        if p is None or len(p) <= index:
            return None
        return float(p[index])

    dc_1x = safe_pred("DC_1X", 1)
    over_25 = safe_pred("Over25", 1)
    btts_yes = safe_pred("BTTS", 1)

    res = {
        "home_team": home_reel,
        "away_team": away_reel,
        "p_h": float(dc_1x * 0.6) if dc_1x is not None else 0.33,
        "p_d": 0.33,
        "p_a": 0.33,
        "dc_1x": dc_1x if dc_1x is not None else 0.5,
        "dc_x2": (1.0 - dc_1x) if dc_1x is not None else 0.5,
        "dc_12": 0.5,
        "over_25": over_25 if over_25 is not None else 0.5,
        "under_25": (1.0 - over_25) if over_25 is not None else 0.5,
        "btts_yes": btts_yes if btts_yes is not None else 0.5,
        "btts_no": (1.0 - btts_yes) if btts_yes is not None else 0.5,
        "best_score": (1, 1),
        "top_scores": [(1, 1, 0.1), (2, 1, 0.08), (1, 2, 0.07)],
        "fiabilite": "⚖️ CONFIANCE MODÉRÉE",
        "ht_prolific": {
            "1ere_mt": safe_pred("HT_Prolific", 1) or 0.33,
            "2eme_mt": safe_pred("HT_Prolific", 2) or 0.33,
            "egalite": safe_pred("HT_Prolific", 0) or 0.33,
        },
        "htr": {
            "1": safe_pred("HTR", 0) or 0.33,
            "N": safe_pred("HTR", 1) or 0.33,
            "2": safe_pred("HTR", 2) or 0.33,
        },
        "analyse_pari": None,
    }

    # Value bet
    if dc_1x is not None:
        options = [("1X", res["dc_1x"]), ("X2", res["dc_x2"]), ("12", res["dc_12"])]
        meilleure = max(options, key=lambda x: x[1])
        cote_bot = round(1 / meilleure[1], 2) if meilleure[1] > 0 else 999

        cote_book = None
        if cotes_book:
            if meilleure[0] == "1X":
                cote_book = cotes_book.get("h")
            elif meilleure[0] == "12":
                cote_book = cotes_book.get("a")
            elif meilleure[0] == "X2":
                cote_book = cotes_book.get("d")

        is_value = bool(cote_book and cote_book > cote_bot)

        res["analyse_pari"] = {
            "label": meilleure[0],
            "proba": meilleure[1],
            "cote_bot": cote_bot,
            "cote_book": cote_book,
            "is_value": is_value,
        }

    return res
