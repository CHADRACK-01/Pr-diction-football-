# core/api/football_data.py
"""
Client Football-Data.org.
- Distinction stricte 400 (paramètres) vs "pas de match"
- Retry avec backoff sur 429/500
- Normalisation compétition = code interne
- Logs enrichis
"""

import time
import requests
from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error, log_warning
from config import FOOTBALL_DATA_KEY

TZ_KINSHASA = timezone(timedelta(hours=1))

COMPETITIONS = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "ligue_1": "FL1",
    "bundesliga_1": "BL1",
    "serie_a": "SA",
    "champions_league": "CL",
}

MAX_RETRIES = 2
BACKOFF_SEC = 2
TIMEOUT = 15


def _extraire_message_erreur(res):
    """Extrait le message d'erreur du body (JSON) si possible."""
    try:
        data = res.json()
        if isinstance(data, dict):
            return data.get("message") or data.get("error") or str(data)[:200]
    except Exception:
        pass
    return res.text[:200] if res.text else ""


def _faire_requete(url, params, contexte_extra):
    """
    Fait une requête avec retry sur 429 et 5xx.
    Retourne (res, tentative) ou (None, tentative_finale).
    """
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}

    for tentative in range(1, MAX_RETRIES + 1):
        try:
            debut = time.time()
            res = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            duree_ms = int((time.time() - debut) * 1000)

            # Succès
            if res.status_code == 200:
                return res, tentative

            # 429 / 5xx : retry
            if res.status_code == 429 or res.status_code >= 500:
                log_warning(
                    message=f"Football-Data HTTP {res.status_code} (tentative {tentative}/{MAX_RETRIES})",
                    module="API",
                    api_context={
                        "source": "football_data",
                        "url": url,
                        "http_status": res.status_code,
                        "http_body": _extraire_message_erreur(res),
                        "attempt": f"{tentative}/{MAX_RETRIES}",
                        "duration_ms": duree_ms,
                    },
                    extra=contexte_extra,
                )
                if tentative < MAX_RETRIES:
                    time.sleep(BACKOFF_SEC * tentative)
                    continue
                return res, tentative

            # 403 : fatal
            if res.status_code == 403:
                log_error(
                    message="Football-Data : accès refusé (clé invalide)",
                    module="API",
                    api_context={
                        "source": "football_data",
                        "url": url,
                        "http_status": 403,
                        "http_body": _extraire_message_erreur(res),
                    },
                    extra=contexte_extra,
                )
                return res, tentative

            # 400 : peut être "pas de match" OU paramètres invalides
            if res.status_code == 400:
                body = _extraire_message_erreur(res).lower()
                # Football-Data renvoie typiquement "No matches found" ou "Invalid date"
                if "no match" in body or "no matches" in body:
                    log_info(
                        f"Football-Data 400 : pas de match pour {contexte_extra.get('competition', '?')}",
                        "API",
                        api_context={
                            "source": "football_data",
                            "url": url,
                            "http_status": 400,
                            "http_body": _extraire_message_erreur(res),
                        },
                    )
                    return res, tentative
                # Sinon : vraie erreur de paramètres
                log_error(
                    message="Football-Data 400 : paramètres invalides",
                    module="API",
                    api_context={
                        "source": "football_data",
                        "url": url,
                        "http_status": 400,
                        "http_body": _extraire_message_erreur(res),
                        "params": params,
                    },
                    extra=contexte_extra,
                )
                return res, tentative

            # Autres 4xx : on loggue et on abandonne
            log_error(
                message=f"Football-Data HTTP inattendu {res.status_code}",
                module="API",
                api_context={
                    "source": "football_data",
                    "url": url,
                    "http_status": res.status_code,
                    "http_body": _extraire_message_erreur(res),
                },
                extra=contexte_extra,
            )
            return res, tentative

        except requests.exceptions.Timeout as e:
            log_warning(
                message=f"Football-Data timeout (tentative {tentative}/{MAX_RETRIES})",
                module="API",
                api_context={
                    "source": "football_data",
                    "url": url,
                    "attempt": f"{tentative}/{MAX_RETRIES}",
                },
                extra=contexte_extra,
                exception=e,
            )
            if tentative < MAX_RETRIES:
                time.sleep(BACKOFF_SEC * tentative)
                continue
            return None, tentative

        except requests.exceptions.ConnectionError as e:
            log_warning(
                message=f"Football-Data connexion impossible (tentative {tentative}/{MAX_RETRIES})",
                module="API",
                api_context={
                    "source": "football_data",
                    "url": url,
                    "attempt": f"{tentative}/{MAX_RETRIES}",
                },
                extra=contexte_extra,
                exception=e,
            )
            if tentative < MAX_RETRIES:
                time.sleep(BACKOFF_SEC * tentative)
                continue
            return None, tentative

        except Exception as e:
            log_error(
                message="Football-Data erreur inattendue",
                module="API",
                api_context={
                    "source": "football_data",
                    "url": url,
                },
                extra=contexte_extra,
                exception=e,
            )
            return None, tentative

    return None, MAX_RETRIES


def recuperer_matchs_bruts():
    """
    Récupère les matchs des 3 prochains jours depuis Football-Data.org.
    Retourne une liste de dicts normalisés.
    """
    log_info("Début de récupération Football-Data.org...", "API")

    if not FOOTBALL_DATA_KEY:
        log_warning(
            message="Football-Data : clé API manquante",
            module="API",
            api_context={"source": "football_data"},
        )
        return []

    date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=3)).strftime("%Y-%m-%d")

    matchs_bruts = []
    erreurs_graves = 0
    competitions_sans_match = 0
    competitions_ok = 0

    for code, comp_code in COMPETITIONS.items():
        url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
        params = {"dateFrom": date_debut, "dateTo": date_fin}
        contexte = {"competition": code, "comp_code": comp_code}

        res, tentative = _faire_requete(url, params, contexte)

        if res is None:
            erreurs_graves += 1
            continue

        if res.status_code == 200:
            try:
                data = res.json()
                matchs_comp = data.get("matches", [])
                count_comp = 0

                for m in matchs_comp:
                    status = m.get("status", "")
                    if status not in ("SCHEDULED", "TIMED"):
                        continue

                    home_team = m.get("homeTeam") or {}
                    away_team = m.get("awayTeam") or {}
                    home_name = home_team.get("name")
                    away_name = away_team.get("name")

                    if not home_name or not away_name:
                        continue

                    cotes_book = None
                    odds = m.get("odds") or {}
                    if isinstance(odds, dict) and "bet365" in odds:
                        b365 = odds["bet365"] or {}
                        if (b365.get("homeWin") and b365.get("draw")
                                and b365.get("awayWin")):
                            cotes_book = {
                                "h": b365.get("homeWin"),
                                "d": b365.get("draw"),
                                "a": b365.get("awayWin"),
                            }

                    matchs_bruts.append({
                        "competition": code,  # code interne
                        "heure": m.get("utcDate"),
                        "home": home_name,
                        "away": away_name,
                        "cotes_book": cotes_book,
                    })
                    count_comp += 1

                competitions_ok += 1
                if count_comp > 0:
                    log_info(
                        f"Football-Data / {code} : {count_comp} matchs",
                        "API",
                        extra={"competition": code, "count": count_comp},
                    )
                else:
                    log_info(
                        f"Football-Data / {code} : aucun match sur la période",
                        "API",
                        extra={"competition": code},
                    )
            except Exception as e:
                log_error(
                    message=f"Football-Data : parse JSON échoué pour {code}",
                    module="API",
                    api_context={
                        "source": "football_data",
                        "url": url,
                        "http_status": 200,
                    },
                    extra=contexte,
                    exception=e,
                )
                erreurs_graves += 1

        elif res.status_code == 400:
            # "Pas de match" : déjà loggué dans _faire_requete
            competitions_sans_match += 1
        else:
            # 403, 429 épuisé, 5xx épuisé
            erreurs_graves += 1

        # Respect du quota : 1s entre chaque requête
        time.sleep(1)

    # Bilan
    if erreurs_graves > 0 and not matchs_bruts:
        log_error(
            message=f"Football-Data : toutes les compétitions ont échoué ({erreurs_graves})",
            module="API",
            extra={
                "erreurs_graves": erreurs_graves,
                "competitions_ok": competitions_ok,
                "sans_match": competitions_sans_match,
            },
        )
    elif matchs_bruts:
        log_info(
            f"Football-Data : {len(matchs_bruts)} matchs au total",
            "API",
            extra={
                "competitions_ok": competitions_ok,
                "sans_match": competitions_sans_match,
            },
        )
    else:
        log_info(
            f"Football-Data : aucun match ({competitions_sans_match} compétitions vides)",
            "API",
        )

    return matchs_bruts


def tester_api():
    """Contrôle de santé : vrai si Football-Data répond avec la clé configurée.

    Une seule requête, sans retry, pour ne pas consommer le quota inutilement.
    """
    if not FOOTBALL_DATA_KEY:
        log_warning(
            message="Football-Data : clé API manquante",
            module="API",
            api_context={"source": "football_data"},
        )
        return False
    try:
        res = requests.get(
            "https://api.football-data.org/v4/competitions",
            headers={"X-Auth-Token": FOOTBALL_DATA_KEY},
            timeout=10,
        )
        if res.status_code == 200:
            log_info("Football-Data : OK", "API")
            return True
        log_warning(
            message=f"Football-Data : statut {res.status_code}",
            module="API",
            api_context={"source": "football_data", "http_status": res.status_code},
        )
        return False
    except Exception as e:
        log_error(
            message="Football-Data : impossible de se connecter",
            module="API",
            api_context={"source": "football_data"},
            exception=e,
        )
        return False
