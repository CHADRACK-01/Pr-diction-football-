# core/api/thesportsdb.py
"""
Client TheSportsDB (fallback dégradé).
⚠️ CORRECTION : normalisation `competition` en code interne via mapping.
Utilisation : uniquement en fallback si les 3 sources principales échouent.
"""

import requests
from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://www.thesportsdb.com/api/v1/json"
API_KEY = "3"  # clé de test publique
TZ_KINSHASA = timezone(timedelta(hours=1))
TIMEOUT = 15


def _normaliser_competition(str_league):
    """
    Convertit un nom de ligue TheSportsDB en code interne connu.
    Ex: "English Premier League" -> "premier_league"
    """
    from config import MAPPING_COMPETITIONS
    if not str_league:
        return "inconnu"

    norm = str_league.strip().lower()

    # Mapping manuel des noms TheSportsDB connus
    correspondances = {
        "english premier league": "premier_league",
        "english league championship": "championship",
        "spanish la liga": "laliga",
        "spanish segunda division": "segunda_division",
        "french ligue 1": "ligue_1",
        "french ligue 2": "ligue_2",
        "german bundesliga": "bundesliga_1",
        "german 2. bundesliga": "bundesliga_2",
        "italian serie a": "serie_a",
        "italian serie b": "serie_b",
        "uefa champions league": "champions_league",
        "uefa europa league": "europa_league",
        "uefa conference league": "conference_league",
    }
    if norm in correspondances:
        return correspondances[norm]

    # Fallback : correspondance via le mapping interne
    noms_vers_codes = {v.lower(): k for k, v in MAPPING_COMPETITIONS.items()}
    if norm in noms_vers_codes:
        return noms_vers_codes[norm]

    return "inconnu"


def tester_api():
    """Vérifie si TheSportsDB répond."""
    try:
        res = requests.get(f"{BASE_URL}/{API_KEY}/all_leagues.php", timeout=TIMEOUT)
        if res.status_code == 200:
            log_info("TheSportsDB : OK", "API")
            return True
        log_warning(
            message=f"TheSportsDB : statut {res.status_code}",
            module="API",
            api_context={"source": "thesportsdb", "http_status": res.status_code},
        )
        return False
    except Exception as e:
        log_error(
            message="TheSportsDB : impossible de se connecter",
            module="API",
            api_context={"source": "thesportsdb"},
            exception=e,
        )
        return False


def get_matchs_du_jour():
    """
    Récupère les matchs du jour via TheSportsDB.
    Utilisé en fallback uniquement.
    """
    try:
        aujourd_hui = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/{API_KEY}/eventsday.php"
        params = {"d": aujourd_hui, "s": "Soccer"}
        res = requests.get(url, params=params, timeout=TIMEOUT)

        if res.status_code != 200:
            log_error(
                message=f"TheSportsDB : erreur {res.status_code}",
                module="API",
                api_context={
                    "source": "thesportsdb",
                    "url": url,
                    "http_status": res.status_code,
                },
            )
            return []

        data = res.json()
        events = data.get("events") or []

        matchs_normalises = []
        for m in events:
            if not isinstance(m, dict):
                continue

            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")
            if not home or not away:
                continue

            # Statut : on ne garde que les matchs à venir
            statut = (m.get("strStatus") or "").lower()
            if statut in ("match finished", "ft", "aet", "pen"):
                continue

            date_match = m.get("dateEvent")
            heure_match = m.get("strTime")
            if date_match and heure_match:
                heure = f"{date_match}T{heure_match}Z"
            else:
                heure = date_match

            competition = _normaliser_competition(m.get("strLeague"))

            matchs_normalises.append({
                "competition": competition,
                "heure": heure,
                "home": home,
                "away": away,
                "cotes_book": None,
            })

        log_info(
            f"TheSportsDB : {len(matchs_normalises)} matchs normalisés",
            "API",
            extra={"total_brut": len(events)},
        )
        return matchs_normalises

    except Exception as e:
        log_error(
            message="TheSportsDB : erreur lors de la récupération",
            module="API",
            api_context={"source": "thesportsdb"},
            exception=e,
        )
        return []


def get_fixtures_by_date(date_str):
    """Récupère les fixtures d'une date (format YYYY-MM-DD)."""
    try:
        url = f"{BASE_URL}/{API_KEY}/eventsday.php"
        params = {"d": date_str, "s": "Soccer"}
        res = requests.get(url, params=params, timeout=TIMEOUT)

        if res.status_code != 200:
            log_error(
                message=f"TheSportsDB fixtures : erreur {res.status_code}",
                module="API",
                api_context={
                    "source": "thesportsdb",
                    "url": url,
                    "http_status": res.status_code,
                },
                extra={"date": date_str},
            )
            return []

        data = res.json()
        events = data.get("events") or []

        matchs = []
        for m in events:
            if not isinstance(m, dict):
                continue
            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")
            if not home or not away:
                continue

            score_home = m.get("intHomeScore")
            score_away = m.get("intAwayScore")
            ftr = None
            if score_home is not None and score_away is not None:
                try:
                    score_home = int(score_home)
                    score_away = int(score_away)
                    ftr = "H" if score_home > score_away else ("A" if score_home < score_away else "D")
                except (ValueError, TypeError):
                    score_home = score_away = None

            matchs.append({
                "competition": _normaliser_competition(m.get("strLeague")),
                "heure": f"{date_str}T{m.get('strTime', '00:00:00')}Z" if m.get("strTime") else date_str,
                "home": home,
                "away": away,
                "cotes_book": None,
                "fthg": score_home,
                "ftag": score_away,
                "ftr": ftr,
            })
        return matchs
    except Exception as e:
        log_error(
            message="TheSportsDB fixtures : erreur",
            module="API",
            api_context={"source": "thesportsdb"},
            extra={"date": date_str},
            exception=e,
        )
        return []
