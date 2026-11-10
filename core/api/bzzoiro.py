import requests
from datetime import datetime, timedelta, timezone
import config
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://sports.bzzoiro.com/api/v2"
TZ_KINSHASA = timezone(timedelta(hours=1))


def _get_headers():
    """Retourne les headers d'authentification Bzzoiro."""
    if not config.BZZOIRO_API_KEY:
        log_warning("Clé API Bzzoiro manquante (BZZOIRO_API_KEY vide)", "BZZOIRO")
        return {"Content-Type": "application/json"}
    return {
        "Authorization": f"Token {config.BZZOIRO_API_KEY}",
        "Content-Type": "application/json"
    }


def tester_api():
    """Vérifie si l'API Bzzoiro répond."""
    try:
        res = requests.get(f"{BASE_URL}/coverage/", headers=_get_headers(), timeout=10)
        if res.status_code == 200:
            log_info("API Bzzoiro : OK", "BZZOIRO")
            return True
        elif res.status_code == 401:
            log_error("API Bzzoiro : clé API invalide (401)", "BZZOIRO")
            return False
        else:
            log_warning(f"API Bzzoiro : Statut {res.status_code}", "BZZOIRO")
            return False
    except requests.exceptions.Timeout:
        log_error("API Bzzoiro : timeout lors du test", "BZZOIRO")
        return False
    except requests.exceptions.ConnectionError as e:
        log_error("API Bzzoiro : impossible de se connecter", "BZZOIRO", exception=e)
        return False
    except Exception as e:
        log_error("API Bzzoiro : erreur inattendue lors du test", "BZZOIRO", exception=e)
        return False


def get_matchs_live():
    """Récupère les matchs en direct (live)."""
    try:
        url = f"{BASE_URL}/events/live/"
        params = {"sport": "football"}
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro live ({res.status_code})", "BZZOIRO")
            return []
        
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        if not isinstance(matchs, list):
            log_warning("Bzzoiro live : format de réponse inattendu", "BZZOIRO")
            return []
        
        log_info(f"{len(matchs)} matchs live récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs
        
    except requests.exceptions.Timeout:
        log_error("Bzzoiro live : timeout", "BZZOIRO")
        return []
    except Exception as e:
        log_error("Erreur Bzzoiro live", "BZZOIRO", exception=e)
        return []


def get_matchs_du_jour():
    """Récupère les matchs du jour (à venir) depuis Bzzoiro."""
    try:
        maintenant = datetime.now(TZ_KINSHASA)
        date_debut = int(maintenant.timestamp())
        date_fin = int((maintenant + timedelta(days=2)).timestamp())
        
        url = f"{BASE_URL}/events/"
        params = {
            "date_from": date_debut,
            "date_to": date_fin,
            "status": "scheduled"
        }
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        
        # Gestion des erreurs HTTP
        if res.status_code == 401:
            log_error("Bzzoiro : clé API invalide (401)", "BZZOIRO")
            return []
        elif res.status_code == 429:
            log_error("Bzzoiro : quota dépassé (429)", "BZZOIRO")
            return []
        elif res.status_code != 200:
            log_error(f"Erreur Bzzoiro matchs ({res.status_code})", "BZZOIRO")
            return []
        
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        if not isinstance(matchs, list):
            log_warning("Bzzoiro : format de réponse inattendu (pas une liste)", "BZZOIRO")
            return []
        
        matchs_normalises = []
        erreurs_parsing = 0
        
        for m in matchs:
            if not isinstance(m, dict):
                erreurs_parsing += 1
                continue
            
            # Extraction robuste des équipes
            home = m.get("home_team")
            if isinstance(home, dict): 
                home = home.get("name")
            if not home:
                erreurs_parsing += 1
                continue
            
            away = m.get("away_team")
            if isinstance(away, dict): 
                away = away.get("name")
            if not away:
                erreurs_parsing += 1
                continue
            
            # Extraction de la compétition
            league = m.get("league")
            comp_name = "Inconnu"
            if league:
                if isinstance(league, dict):
                    comp_name = league.get("name", "Inconnu")
                else:
                    comp_name = str(league)
            
            # Extraction des cotes
            odds = m.get("odds")
            cotes = None
            if isinstance(odds, dict):
                h = odds.get("home_win")
                d = odds.get("draw")
                a = odds.get("away_win")
                if h and d and a:
                    cotes = {"h": h, "d": d, "a": a}
            
            # Extraction de l'heure
            heure = None
            for key in ["start_time", "start_date", "datetime", "date", "time", "utcDate"]:
                if m.get(key):
                    heure = m.get(key)
                    break
            
            matchs_normalises.append({
                "competition": comp_name,
                "heure": heure,
                "home": home,
                "away": away,
                "cotes_book": cotes
            })
        
        if erreurs_parsing > 0:
            log_warning(f"Bzzoiro : {erreurs_parsing} matchs ignorés (données incomplètes)", "BZZOIRO")
        
        log_info(f"{len(matchs_normalises)} matchs récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs_normalises
        
    except requests.exceptions.Timeout:
        log_error("Bzzoiro : timeout lors de la récupération des matchs", "BZZOIRO")
        return []
    except requests.exceptions.ConnectionError as e:
        log_error("Bzzoiro : impossible de se connecter", "BZZOIRO", exception=e)
        return []
    except Exception as e:
        log_error("Erreur Bzzoiro matchs", "BZZOIRO", exception=e)
        return []
