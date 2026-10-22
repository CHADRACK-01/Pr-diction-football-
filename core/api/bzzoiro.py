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
    """Vérifie si l'API Bzzoiro répond."""
    try:
        res = requests.get(f"{BASE_URL}/coverage/", headers=_get_headers(), timeout=10)
        if res.status_code == 200:
            log_info("API Bzzoiro : OK", "BZZOIRO")
            return True
        log_warning(f"API Bzzoiro : Statut {res.status_code}", "BZZOIRO")
        return False
    except Exception as e:
        log_error(f"API Bzzoiro injoignable : {e}", "BZZOIRO")
        return False


def get_matchs_live():
    """Récupère les matchs en direct."""
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
        log_error(f"Erreur Bzzoiro live : {e}", "BZZOIRO")
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
        
        if res.status_code != 200:
            log_error(f"Erreur Bzzoiro matchs ({res.status_code})", "BZZOIRO")
            return []
        
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        matchs_normalises = []
        for m in matchs:
            # Extraction robuste des équipes
            home = m.get("home_team")
            if isinstance(home, dict): home = home.get("name")
            away = m.get("away_team")
            if isinstance(away, dict): away = away.get("name")
            
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
                cotes = {
                    "h": odds.get("home_win"),
                    "d": odds.get("draw"),
                    "a": odds.get("away_win")
                }
            
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
        
        log_info(f"{len(matchs_normalises)} matchs récupérés depuis Bzzoiro.", "BZZOIRO")
        return matchs_normalises
    except Exception as e:
        log_error(f"Erreur Bzzoiro matchs : {e}", "BZZOIRO")
        return []


# =========================================================
# DÉCOUVERTE DES LIGUES
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
        log_error(f"Erreur lors de la recherche des ligues : {e}", "BZZOIRO")
        return []
