import requests
from datetime import datetime, timedelta, timezone
import config
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://sports.bzzoiro.com/api/v2"
TZ_KINSHASA = timezone(timedelta(hours=1))

def _get_headers():
    """Prépare les headers d'authentification."""
    return {
        "Authorization": f"Token {config.BZZOIRO_API_KEY}",
        "Content-Type": "application/json"
    }

def tester_api():
    """Vérifie si l'API Bzzoiro répond (endpoint coverage, ne nécessite pas de clé)."""
    try:
        res = requests.get(f"{BASE_URL}/coverage/", timeout=10)
        if res.status_code == 200:
            log_info("API Bzzoiro : OK", "BZZOIRO")
            return True
        log_warning(f"API Bzzoiro : Statut {res.status_code}", "BZZOIRO")
        return False
    except Exception as e:
        log_error(f"API Bzzoiro injoignable : {e}", "BZZOIRO")
        return False

def get_matchs_live():
    """Récupère les matchs de football en direct."""
    try:
        url = f"{BASE_URL}/events/live/"
        params = {"sport": "football"} # Filtre pour ne garder que le foot
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro live ({res.status_code})", "BZZOIRO")
            return []
            
        data = res.json()
        # L'API retourne parfois un dict avec 'results' ou directement une liste
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        log_info(f"{len(matchs)} matchs live récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs
    except Exception as e:
        log_error(f"Erreur Bzzoiro live : {e}", "BZZOIRO", e)
        return []

def get_matchs_du_jour():
    """Récupère les matchs à venir pour aujourd'hui et demain."""
    try:
        date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
        date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=2)).strftime("%Y-%m-%d")
        
        url = f"{BASE_URL}/events/"
        params = {
            "sport": "football",
            "date_from": date_debut,
            "date_to": date_fin,
            "status": "scheduled" # Uniquement les matchs pas encore commencés
        }
        
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro matchs ({res.status_code})", "BZZOIRO")
            return []
            
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        # Normalisation des données pour qu'elles correspondent à notre format interne
        matchs_normalises = []
        for m in matchs:
            try:
                # On extrait les infos dont on a besoin
                matchs_normalises.append({
                    "competition": m.get("league", {}).get("name", "Inconnu"),
                    "heure": m.get("start_time"),
                    "home": m.get("home_team", {}).get("name"),
                    "away": m.get("away_team", {}).get("name"),
                    "cotes_book": { # On récupère les cotes si dispo dans l'event
                        "h": m.get("odds", {}).get("home_win"),
                        "d": m.get("odds", {}).get("draw"),
                        "a": m.get("odds", {}).get("away_win")
                    } if m.get("odds") else None
                })
            except Exception:
                continue
                
        log_info(f"{len(matchs_normalises)} matchs récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs_normalises
        
    except Exception as e:
        log_error(f"Erreur Bzzoiro matchs : {e}", "BZZOIRO", e)
        return []
