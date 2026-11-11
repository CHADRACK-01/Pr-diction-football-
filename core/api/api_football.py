# core/api/api_football.py
"""
Client API-Football (round-robin sur plusieurs clés).
⚠️ IMPORTANT : get_live_matches n'est PLUS utilisé comme source de collecte.
Il reste disponible pour les stats détaillées d'un match live.
"""

import time
import requests
from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error, log_warning
from config import API_FOOTBALL_KEYS

BASE_URL = "https://v3.football.api-sports.io"
TZ_KINSHASA = timezone(timedelta(hours=1))
TIMEOUT = 15

_current_key_index = 0
_key_lock = __import__("threading").Lock()


def _get_next_key():
    """Retourne la prochaine clé en round-robin (thread-safe)."""
    global _current_key_index
    with _key_lock:
        if not API_FOOTBALL_KEYS:
            return None
        key = API_FOOTBALL_KEYS[_current_key_index]
        _current_key_index = (_current_key_index + 1) % len(API_FOOTBALL_KEYS)
        return key


def _get_headers(key):
    return {"x-apisports-key": key}


def _extraire_message_erreur(res):
    try:
        data = res.json()
        if isinstance(data, dict):
            errors = data.get("errors")
            if isinstance(errors, dict):
                return ", ".join(f"{k}: {v}" for k, v in errors.items())[:200]
            return str(errors or data)[:200]
    except Exception:
        pass
    return res.text[:200] if res.text else ""


def _faire_requete(url, contexte_extra):
    """
    Requête avec round-robin et fallback 429.
    Retourne (res, key_utilisee).
    """
    key = _get_next_key()
    if not key:
        log_warning(
            message="API-Football : aucune clé configurée",
            module="API",
            api_context={"source": "api_football"},
        )
        return None, None

    try:
        debut = time.time()
        res = requests.get(url, headers=_get_headers(key), timeout=TIMEOUT)
        duree_ms = int((time.time() - debut) * 1000)

        if res.status_code == 429 and len(API_FOOTBALL_KEYS) > 1:
            log_warning(
                message="API-Football : quota dépassé (429), bascule clé suivante",
                module="API",
                api_context={
                    "source": "api_football",
                    "url": url,
                    "http_status": 429,
                    "duration_ms": duree_ms,
                },
                extra=contexte_extra,
            )
            key = _get_next_key()
            if key:
                res = requests.get(url, headers=_get_headers(key), timeout=TIMEOUT)

        return res, key

    except requests.exceptions.Timeout as e:
        log_warning(
            message="API-Football : timeout",
            module="API",
            api_context={"source": "api_football", "url": url},
            extra=contexte_extra,
            exception=e,
        )
        return None, key
    except Exception as e:
        log_error(
            message="API-Football : erreur réseau",
            module="API",
            api_context={"source": "api_football", "url": url},
            extra=contexte_extra,
            exception=e,
        )
        return None, key


def tester_api():
    """Vérifie si au moins une clé répond."""
    if not API_FOOTBALL_KEYS:
        log_warning(
            message="API-Football : aucune clé configurée",
            module="API",
            api_context={"source": "api_football"},
        )
        return False

    for i, key in enumerate(API_FOOTBALL_KEYS):
        try:
            res = requests.get(
                f"{BASE_URL}/status",
                headers=_get_headers(key),
                timeout=10,
            )
            if res.status_code == 200:
                data = res.json()
                req = data.get("response", {}).get("requests", {})
                used = req.get("current", 0)
                limit = req.get("limit_day", 100)
                log_info(
                    f"API-Football clé {i + 1} : OK ({used}/{limit})",
                    "API",
                )
                return True
            elif res.status_code == 429:
                log_warning(
                    message=f"API-Football clé {i + 1} : quota dépassé",
                    module="API",
                    api_context={
                        "source": "api_football",
                        "http_status": 429,
                    },
                )
            else:
                log_warning(
                    message=f"API-Football clé {i + 1} : statut {res.status_code}",
                    module="API",
                    api_context={
                        "source": "api_football",
                        "http_status": res.status_code,
                    },
                )
        except Exception as e:
            log_error(
                message=f"API-Football clé {i + 1} : connexion échouée",
                module="API",
                api_context={"source": "api_football"},
                exception=e,
            )

    return False


def get_match_stats(fixture_id):
    """Récupère les stats détaillées d'un match."""
    url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    res, _ = _faire_requete(url, {"fixture_id": fixture_id})

    if not res or res.status_code != 200:
        log_error(
            message=f"API-Football : stats indisponibles pour fixture {fixture_id}",
            module="API",
            api_context={
                "source": "api_football",
                "url": url,
                "http_status": res.status_code if res else None,
            },
            extra={"fixture_id": fixture_id},
        )
        return {}

    try:
        data = res.json()
        stats = data.get("response", [])
        if not stats:
            return {}

        resultat = {}
        for equipe_stats in stats:
            equipe_nom = equipe_stats.get("team", {}).get("name", "")
            for stat in equipe_stats.get("statistics", []):
                type_stat = stat.get("type")
                valeur = stat.get("value")
                if type_stat and valeur is not None:
                    resultat[f"{equipe_nom}_{type_stat}"] = valeur
        return resultat
    except Exception as e:
        log_error(
            message=f"API-Football : parse stats échoué pour fixture {fixture_id}",
            module="API",
            api_context={"source": "api_football"},
            extra={"fixture_id": fixture_id},
            exception=e,
        )
        return {}


def get_fixtures_by_date(date_str):
    """Récupère les fixtures d'une date."""
    url = f"{BASE_URL}/fixtures?date={date_str}"
    res, _ = _faire_requete(url, {"operation": "fixtures_by_date", "date": date_str})

    if not res or res.status_code != 200:
        log_error(
            message=f"API-Football : fixtures indisponibles pour {date_str}",
            module="API",
            api_context={
                "source": "api_football",
                "url": url,
                "http_status": res.status_code if res else None,
            },
            extra={"date": date_str},
        )
        return []

    try:
        return res.json().get("response", [])
    except Exception as e:
        log_error(
            message=f"API-Football : parse fixtures échoué pour {date_str}",
            module="API",
            api_context={"source": "api_football"},
            extra={"date": date_str},
            exception=e,
        )
        return []


def get_fixtures_by_league(league_id, season, date_from=None, date_to=None):
    """Récupère les fixtures d'une ligue et saison."""
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    if date_from:
        url += f"&from={date_from}"
    if date_to:
        url += f"&to={date_to}"

    res, _ = _faire_requete(url, {"league_id": league_id, "season": season})

    if not res or res.status_code != 200:
        log_error(
            message=f"API-Football : fixtures indisponibles ligue {league_id}",
            module="API",
            api_context={
                "source": "api_football",
                "url": url,
                "http_status": res.status_code if res else None,
            },
            extra={"league_id": league_id, "season": season},
        )
        return []

    try:
        return res.json().get("response", [])
    except Exception as e:
        log_error(
            message=f"API-Football : parse fixtures échoué ligue {league_id}",
            module="API",
            api_context={"source": "api_football"},
            extra={"league_id": league_id},
            exception=e,
        )
        return []
