# core/results_checker.py
"""
Vérification des résultats des pronostics de la veille.
- date_match en Kinshasa (pas UTC)
- est_gagnant : NULL (à vérifier), 1 (gagné), 0 (perdu), -1 (abandonné)
- Limite de MAX_TENTATIVES tentatives, puis abandon explicite (est_gagnant = -1)
- Normalisation robuste des noms
"""

import unicodedata
import requests
from datetime import datetime, timedelta, timezone

from users.db import db_fetchone, db_fetchall, db_execute
from config import FOOTBALL_DATA_KEY
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))
MAX_TENTATIVES = 5

# Valeur sentinelle : pronostic abandonné (résultat introuvable après N essais)
STATUT_ABANDONNE = -1

PREFIXES_SUFFIXES = [
    "fc", "afc", "cf", "sc", "ac", "as", "ss", "us", "rc", "rcd",
    "ca", "ud", "cd", "sd", "sco", "hsc", "sv", "vfl", "vfb", "tsg",
    "fsv", "ssv", "1.", "1900", "1901", "1909", "1913", "1848", "1899",
    "1919", "1846", "1898", "bsc", "aj", "sco", "usl", "csm",
]


def _normaliser_nom(nom):
    """Normalise un nom d'équipe pour le matching."""
    if not nom:
        return ""
    try:
        nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("utf-8")
        nom = nom.lower().strip()
        mots = nom.split()
        mots_filtres = [m for m in mots if m not in PREFIXES_SUFFIXES]
        if not mots_filtres:
            mots_filtres = mots
        return "".join(mots_filtres).replace(" ", "")
    except Exception as e:
        log_warning(
            message=f"Impossible de normaliser '{nom}'",
            module="RESULTS",
            extra={"nom": str(nom)[:100]},
            exception=e,
        )
        return str(nom).lower().strip()


def _extraire_scores(match_api):
    """Extrait (score_home, score_away) full-time ou (None, None)."""
    try:
        score = match_api.get("score", {}) or {}
        full_time = score.get("fullTime", {}) or {}
        home = full_time.get("home")
        away = full_time.get("away")
        if home is None or away is None:
            return None, None
        return int(home), int(away)
    except (ValueError, TypeError):
        return None, None
    except Exception:
        return None, None


def _recuperer_resultats_api(date_str):
    """Récupère les matchs FINISHED d'une date via Football-Data."""
    if not FOOTBALL_DATA_KEY:
        log_warning(
            message="Football-Data : clé manquante pour vérification",
            module="RESULTS",
            api_context={"source": "football_data"},
        )
        return {}

    url = "https://api.football-data.org/v4/matches"
    params = {"dateFrom": date_str, "dateTo": date_str}
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code != 200:
            log_error(
                message=f"Football-Data : erreur {res.status_code} pour {date_str}",
                module="RESULTS",
                api_context={
                    "source": "football_data",
                    "url": url,
                    "http_status": res.status_code,
                },
                extra={"date": date_str},
            )
            return {}
        matchs_api = res.json().get("matches", [])
    except requests.exceptions.Timeout as e:
        log_error(
            message="Football-Data : timeout pour vérification",
            module="RESULTS",
            api_context={"source": "football_data", "url": url},
            extra={"date": date_str},
            exception=e,
        )
        return {}
    except Exception as e:
        log_error(
            message="Football-Data : erreur réseau pour vérification",
            module="RESULTS",
            extra={"date": date_str},
            exception=e,
        )
        return {}

    resultats = {}
    for m in matchs_api:
        try:
            if m.get("status") != "FINISHED":
                continue
            home = _normaliser_nom(m.get("homeTeam", {}).get("name", ""))
            away = _normaliser_nom(m.get("awayTeam", {}).get("name", ""))
            if not home or not away:
                continue
            sh, sa = _extraire_scores(m)
            if sh is None or sa is None:
                continue
            resultats[f"{home}_{away}"] = (sh, sa)
        except Exception as e:
            log_warning(
                message="Erreur de parsing d'un match API",
                module="RESULTS",
                exception=e,
            )
            continue

    log_info(
        f"{len(resultats)} résultats récupérés pour {date_str}",
        "RESULTS",
        extra={"date": date_str},
    )
    return resultats


def _evaluer_pronostic(reco, sh, sa):
    """Retourne True/False selon que le pronostic est gagnant/perdant."""
    if reco == "1X" and sh >= sa:
        return True
    if reco == "X2" and sa >= sh:
        return True
    if reco == "12" and sh != sa:
        return True
    return False


def verifier_resultats_veille():
    """
    Vérifie les pronostics de la veille.

    - Ne traite que les pronostics non encore résolus (est_gagnant IS NULL)
      ET encore en cours de vérification (tentatives < MAX_TENTATIVES).
    - Marque est_gagnant = -1 (STATUT_ABANDONNE) après MAX_TENTATIVES échecs.
    - Retourne {total, gagnes, pourcentage, texte}.
    """
    hier = (datetime.now(TZ_KINSHASA) - timedelta(days=1)).strftime("%Y-%m-%d")

    if not FOOTBALL_DATA_KEY:
        return {
            "total": 0, "gagnes": 0, "pourcentage": 0,
            "texte": "❌ Clé API manquante.",
        }

    # 1. Lire les pronostics non vérifiés ET encore en cours (pas abandonnés)
    pronos = db_fetchall(
        """
        SELECT id, home_team, away_team, pronostic_reco, tentatives_verification
        FROM resultats_pronostics
        WHERE date_match = ?
          AND est_gagnant IS NULL
          AND COALESCE(tentatives_verification, 0) < ?
        """,
        params=[hier, MAX_TENTATIVES],
        db_context={"table": "resultats_pronostics", "operation": "list_verif"},
    )

    if not pronos:
        log_info("Aucun pronostic à vérifier pour hier", "RESULTS")
        return {
            "total": 0, "gagnes": 0, "pourcentage": 0,
            "texte": "Aucun pronostic à vérifier hier.",
        }

    # 2. Récupérer les résultats API
    resultats_api = _recuperer_resultats_api(hier)

    # 3. Comparer
    gagnes = 0
    total = 0
    non_trouves = 0
    a_mettre_a_jour = []  # (id, est_gagnant, tentatives)
    a_abandonner = []     # (id, tentatives)

    for p in pronos:
        try:
            p_id, home, away, reco, tentatives = p
            tentatives = tentatives or 0
            total += 1

            home_norm = _normaliser_nom(home)
            away_norm = _normaliser_nom(away)
            api_key = f"{home_norm}_{away_norm}"

            if api_key in resultats_api:
                sh, sa = resultats_api[api_key]
                est_gagnant_bool = _evaluer_pronostic(reco, sh, sa)

                if est_gagnant_bool:
                    gagnes += 1

                a_mettre_a_jour.append(
                    (int(est_gagnant_bool), tentatives + 1, p_id)
                )
            else:
                non_trouves += 1
                nouvelle_tentative = tentatives + 1
                if nouvelle_tentative >= MAX_TENTATIVES:
                    a_abandonner.append((nouvelle_tentative, p_id))
                else:
                    a_mettre_a_jour.append((None, nouvelle_tentative, p_id))
        except Exception as e:
            log_warning(
                message="Erreur de comparaison d'un pronostic",
                module="RESULTS",
                extra={"pronostic_id": p[0] if p else "?"},
                exception=e,
            )
            continue

    # 4. Mettre à jour la BDD
    for est_gagnant, tentatives, p_id in a_mettre_a_jour:
        db_execute(
            """
            UPDATE resultats_pronostics
            SET est_gagnant = ?, tentatives_verification = ?
            WHERE id = ?
            """,
            params=[est_gagnant, tentatives, p_id],
            db_context={"table": "resultats_pronostics", "operation": "update_verif"},
        )

    for tentatives, p_id in a_abandonner:
        db_execute(
            """
            UPDATE resultats_pronostics
            SET est_gagnant = ?, tentatives_verification = ?
            WHERE id = ?
            """,
            params=[STATUT_ABANDONNE, tentatives, p_id],
            db_context={"table": "resultats_pronostics", "operation": "abandon_verif"},
        )
        log_warning(
            message=f"Pronostic #{p_id} abandonné après {tentatives} tentatives",
            module="RESULTS",
            extra={"pronostic_id": p_id, "tentatives": tentatives},
        )

    # 5. Message canal
    pourcentage = round((gagnes / total) * 100, 1) if total > 0 else 0
    if pourcentage >= 70:
        emoji = "🔥"
    elif pourcentage >= 50:
        emoji = "✅"
    else:
        emoji = "📉"

    texte_canal = (
        f"{emoji} **BILAN DE LA VEILLE** {emoji}\n\n"
        f"✅ Pronostics gagnants : {gagnes}/{total}\n"
        f"🎯 Taux de réussite : **{pourcentage}%**\n"
    )
    if non_trouves > 0:
        texte_canal += f"\n⚠️ {non_trouves} pronostic(s) sans résultat API\n"
    texte_canal += (
        "\n👉 Rejoignez-nous pour les pronostics du jour : "
        "@MonPronosticFootball_bot"
    )

    log_info(
        f"Résultats vérifiés : {gagnes}/{total} ({pourcentage}%)",
        "RESULTS",
        extra={"gagnes": gagnes, "total": total, "non_trouves": non_trouves},
    )
    return {
        "total": total, "gagnes": gagnes,
        "pourcentage": pourcentage, "texte": texte_canal,
    }
