import requests
from datetime import datetime, timedelta, timezone
import config
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://sports.bzzoiro.com/api/v2"
TZ_KINSHASA = timezone(timedelta(hours=1))

def _get_headers():
    return {
        "Authorization": f"Token {config.BZZOIRO_API_KEY}",
        "Content-Type": "application/json"
    }

def tester_api():
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
    try:
        url = f"{BASE_URL}/events/live/"
        params = {"sport": "football"}
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro live ({res.status_code})", "BZZOIRO")
            return []
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        log_info(f"{len(matchs)} matchs live récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs
    except Exception as e:
        log_error(f"Erreur Bzzoiro live : {e}", "BZZOIRO", e)
        return []

def get_matchs_du_jour():
    try:
        date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
        date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=2)).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/events/"
        params = {
            "sport": "football",
            "date_from": date_debut,
            "date_to": date_fin,
            "status": "scheduled"
        }
        res = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro matchs ({res.status_code})", "BZZOIRO")
            return []
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        matchs_normalises = []
        for m in matchs:
            try:
                matchs_normalises.append({
                    "competition": m.get("league", {}).get("name", "Inconnu"),
                    "heure": m.get("start_time"),
                    "home": m.get("home_team", {}).get("name"),
                    "away": m.get("away_team", {}).get("name"),
                    "cotes_book": {
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

# =========================================================
# NOUVEAU : DÉCOUVERTE DES LIGUES
# =========================================================
def lister_ligues_europeennes():
    """
    Liste les ligues disponibles dans Bzzoiro et affiche celles qui 
    concernent les compétitions européennes (C1, C3, C4).
    """
    log_info("Recherche des ligues européennes dans Bzzoiro...", "BZZOIRO")
    try:
        url = f"{BASE_URL}/leagues/"
        res = requests.get(url, headers=_get_headers(), timeout=15)
        
        if res.status_code != 200:
            log_error(f"Erreur API Ligues ({res.status_code})", "BZZOIRO")
            return []
            
        data = res.json()
        ligues = data.get("results", data) if isinstance(data, dict) else data
        
        # Mots-clés pour identifier les compétitions européennes
        mots_cles = ["champions league", "europa", "conference", "uefa"]
        
        ligues_europeennes = []
        for ligue in ligues:
            nom = ligue.get("name", "").lower()
            if any(mot in nom for mot in mots_cles):
                ligues_europeennes.append({
                    "id": ligue.get("id"),
                    "nom": ligue.get("name"),
                    "pays": ligue.get("country", "Europe"),
                    "saison_actuelle": ligue.get("current_season", "N/A")
                })
                log_info(f"Ligue trouvée : {ligue.get('name')} (ID: {ligue.get('id')})", "BZZOIRO")
        
        if not ligues_europeennes:
            log_warning("Aucune compétition européenne trouvée dans Bzzoiro.", "BZZOIRO")
        else:
            log_info(f"{len(ligues_europeennes)} compétitions européennes trouvées.", "BZZOIRO")
            
        return ligues_europeennes
        
    except Exception as e:
        log_error(f"Erreur lors de la recherche des ligues : {e}", "BZZOIRO", e)
        return []
