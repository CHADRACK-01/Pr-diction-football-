import requests
from datetime import datetime, timedelta, timezone
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://www.thesportsdb.com/api/v1/json"
# La clé "3" est une clé de test publique pour TheSportsDB
# Pour la production, tu peux demander une clé gratuite sur patreon
API_KEY = "3"
TZ_KINSHASA = timezone(timedelta(hours=1))


def _get_headers():
    """Retourne les headers (TheSportsDB n'en a pas besoin, mais on garde la structure)."""
    return {}


def tester_api():
    """Vérifie si TheSportsDB répond."""
    try:
        res = requests.get(f"{BASE_URL}/{API_KEY}/all_leagues.php", timeout=10)
        if res.status_code == 200:
            log_info("TheSportsDB : OK", "THESPORTSDB")
            return True
        else:
            log_warning(f"TheSportsDB : Statut {res.status_code}", "THESPORTSDB")
            return False
    except Exception as e:
        log_error("TheSportsDB : impossible de se connecter", "THESPORTSDB", exception=e)
        return False


def get_live_matches():
    """
    Récupère les matchs en direct (live).
    Utilise l'endpoint livescore.php.
    """
    try:
        url = f"{BASE_URL}/{API_KEY}/livescore.php?s=Soccer"
        res = requests.get(url, timeout=15)
        
        if res.status_code != 200:
            log_error(f"TheSportsDB live : erreur {res.status_code}", "THESPORTSDB")
            return []
        
        data = res.json()
        matchs = data.get("events", []) or []
        
        matchs_normalises = []
        for m in matchs:
            # Extraction sécurisée
            home = m.get("strHomeTeam")
            away = m.get("strAwayTeam")
            if not home or not away:
                continue
            
            # Date du match (format : "2026-11-11")
            date_match = m.get("dateEvent")
            heure_match = m.get("strTime")
            
            if date_match and heure_match:
                try:
                    heure = f"{date_match}T{heure_match}Z"
                except:
                    heure = date_match
            else:
                heure = date_match
            
            # Scores
            score_home = m.get("intHomeScore")
            score_away = m.get("intAwayScore")
            
            # Résultat
            ftr = None
            if score_home is not None and score_away is not None:
                score_home = int(score_home)
                score_away = int(score_away)
                if score_home > score_away: ftr = 'H'
                elif score_home < score_away: ftr = 'A'
                else: ftr = 'D'
            
            matchs_normalises.append({
                "competition": m.get("strLeague", "Inconnu"),
                "heure": heure,
                "home": home,
                "away": away,
                "cotes_book": None,  # TheSportsDB ne fournit pas de cotes
                "fthg": score_home,
                "ftag": score_away,
                "ftr": ftr,
                "hthg": m.get("intHomeScoreHT"),
                "htag": m.get("intAwayScoreHT"),
                "htr": None,
            })
        
        log_info(f"{len(matchs_normalises)} matchs live récupérés depuis TheSportsDB.", "THESPORTSDB")
        return matchs_normalises
    except Exception as e:
        log_error("Erreur TheSportsDB live", "THESPORTSDB", exception=e)
        return []


def get_fixtures_by_date(date_str):
    """
    Récupère les matchs d'une date (format YYYY-MM-DD).
    Utile pour les résultats historiques.
    """
    try:
        url = f"{BASE_URL}/{API_KEY}/eventsday.php?d={date_str}&s=Soccer"
        res = requests.get(url, timeout=15)
        
        if res.status_code != 200:
            log_error(f"TheSportsDB fixtures : erreur {res.status_code} pour {date_str}", "THESPORTSDB")
            return []
        
        data = res.json()
        matchs = data.get("events", []) or []
        
        matchs_normalises = []
        for m in matchs:
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
                    if score_home > score_away: ftr = 'H'
                    elif score_home < score_away: ftr = 'A'
                    else: ftr = 'D'
                except (ValueError, TypeError):
                    score_home = None
                    score_away = None
            
            matchs_normalises.append({
                "competition": m.get("strLeague", "Inconnu"),
                "heure": f"{date_str}T{m.get('strTime', '00:00:00')}Z" if m.get('strTime') else date_str,
                "home": home,
                "away": away,
                "cotes_book": None,
                "fthg": score_home,
                "ftag": score_away,
                "ftr": ftr,
                "hthg": m.get("intHomeScoreHT"),
                "htag": m.get("intAwayScoreHT"),
                "htr": None,
            })
        
        return matchs_normalises
    except Exception as e:
        log_error(f"Erreur TheSportsDB fixtures pour {date_str}", "THESPORTSDB", exception=e)
        return []
