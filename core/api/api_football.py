import requests
from datetime import datetime, timedelta, timezone
import config
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://v3.football.api-sports.io"
TZ_KINSHASA = timezone(timedelta(hours=1))

# Index de la clé actuelle (pour le round-robin)
_current_key_index = 0


def _get_next_key():
    """
    Retourne la prochaine clé API-Football en mode round-robin.
    Si une clé est épuisée, on passe à la suivante.
    """
    global _current_key_index
    
    if not config.API_FOOTBALL_KEYS:
        log_error("Aucune clé API-Football configurée", "API_FOOTBALL")
        return None
    
    # On récupère la clé à l'index actuel
    key = config.API_FOOTBALL_KEYS[_current_key_index]
    
    # On passe à la clé suivante pour la prochaine requête
    _current_key_index = (_current_key_index + 1) % len(config.API_FOOTBALL_KEYS)
    
    return key


def _get_headers(key):
    """Retourne les headers d'authentification pour une clé donnée."""
    return {"x-apisports-key": key}


def tester_api():
    """Vérifie si au moins une clé API-Football répond."""
    for i, key in enumerate(config.API_FOOTBALL_KEYS):
        try:
            res = requests.get(f"{BASE_URL}/status", headers=_get_headers(key), timeout=10)
            if res.status_code == 200:
                data = res.json()
                requests_used = data.get("response", {}).get("requests", {}).get("current", 0)
                requests_limit = data.get("response", {}).get("requests", {}).get("limit_day", 100)
                log_info(f"API-Football clé {i+1} : OK ({requests_used}/{requests_limit} requêtes utilisées)", "API_FOOTBALL")
                return True
            elif res.status_code == 429:
                log_warning(f"API-Football clé {i+1} : quota dépassé (429)", "API_FOOTBALL")
            else:
                log_warning(f"API-Football clé {i+1} : statut {res.status_code}", "API_FOOTBALL")
        except Exception as e:
            log_error(f"API-Football clé {i+1} : impossible de se connecter", "API_FOOTBALL", exception=e)
    
    return False


def get_live_matches():
    """
    Récupère les matchs en direct (live).
    Utilise le round-robin sur les clés pour éviter le quota.
    """
    try:
        key = _get_next_key()
        if not key:
            return []
        
        url = f"{BASE_URL}/fixtures?live=all"
        res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code == 429:
            log_warning("API-Football live : quota dépassé, on tente la clé suivante", "API_FOOTBALL")
            key = _get_next_key()
            if key:
                res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code != 200:
            log_error(f"API-Football live : erreur {res.status_code}", "API_FOOTBALL")
            return []
        
        data = res.json()
        matchs = data.get("response", [])
        
        # On filtre uniquement le football (pas les autres sports)
        matchs = [m for m in matchs if m.get("league", {}).get("sport") == "football"]
        
        log_info(f"{len(matchs)} matchs live récupérés depuis API-Football.", "API_FOOTBALL")
        return matchs
    except Exception as e:
        log_error("Erreur API-Football live", "API_FOOTBALL", exception=e)
        return []


def get_match_stats(fixture_id):
    """
    Récupère les statistiques détaillées d'un match via son ID.
    Utilise le round-robin sur les clés.
    """
    try:
        key = _get_next_key()
        if not key:
            return {}
        
        url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
        res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code == 429:
            log_warning("API-Football stats : quota dépassé, on tente la clé suivante", "API_FOOTBALL")
            key = _get_next_key()
            if key:
                res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code != 200:
            log_error(f"API-Football stats : erreur {res.status_code} pour fixture {fixture_id}", "API_FOOTBALL")
            return {}
        
        data = res.json()
        stats = data.get("response", [])
        
        if not stats:
            return {}
        
        # On normalise les statistiques dans un dictionnaire
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
        log_error(f"Erreur API-Football stats pour fixture {fixture_id}", "API_FOOTBALL", exception=e)
        return {}


def get_fixtures_by_date(date_str):
    """
    Récupère les matchs d'une date donnée (format YYYY-MM-DD).
    Utile pour les résultats historiques.
    """
    try:
        key = _get_next_key()
        if not key:
            return []
        
        url = f"{BASE_URL}/fixtures?date={date_str}"
        res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code == 429:
            log_warning("API-Football fixtures : quota dépassé, on tente la clé suivante", "API_FOOTBALL")
            key = _get_next_key()
            if key:
                res = requests.get(url, headers=_get_headers(key), timeout=15)
        
        if res.status_code != 200:
            log_error(f"API-Football fixtures : erreur {res.status_code} pour {date_str}", "API_FOOTBALL")
            return []
        
        data = res.json()
        return data.get("response", [])
    except Exception as e:
        log_error(f"Erreur API-Football fixtures pour {date_str}", "API_FOOTBALL", exception=e)
        return []
