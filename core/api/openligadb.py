import requests
from datetime import datetime, timezone, timedelta
from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://api.openligadb.de"
TZ_KINSHASA = timezone(timedelta(hours=1))

LIGUES_OPENLIGADB = {
    "bl1": "bundesliga_1",
    "bl2": "bundesliga_2",
}


def tester_api():
    """Vérifie si l'API OpenLigaDB répond."""
    res = requests.get(f"{BASE_URL}/getavailableleagues", timeout=10)
    if res.status_code == 200:
        log_info("API OpenLigaDB : OK", "OPENLIGADB")
        return True
    log_warning(f"API OpenLigaDB : Statut {res.status_code}", "OPENLIGADB")
    return False


def get_matchs_du_jour():
    """
    Récupère les matchs de Bundesliga (bl1) pour la journée en cours.
    OpenLigaDB fonctionne par journée (matchday), pas par date exacte.
    On récupère donc la journée la plus récente.
    """
    matchs_normalises = []
    
    now = datetime.now(TZ_KINSHASA)
    saison = now.year if now.month >= 7 else now.year - 1
    
    for shortcut, comp_code in LIGUES_OPENLIGADB.items():
        url = f"{BASE_URL}/getmatchdata/{shortcut}/{saison}/1"
        res = requests.get(url, timeout=15)
        
        if res.status_code != 200:
            log_warning(f"OpenLigaDB : Pas de données pour {shortcut}", "OPENLIGADB")
            continue
            
        data = res.json()
        if not isinstance(data, list):
            continue
            
        for m in data:
            if m.get("matchIsFinished"):
                continue
                
            matchs_normalises.append({
                "competition": comp_code,
                "heure": m.get("matchDateTimeUTC"),
                "home": m.get("team1", {}).get("teamName"),
                "away": m.get("team2", {}).get("teamName"),
                "cotes_book": None,
                "logo_home": m.get("team1", {}).get("teamIconUrl"),
                "logo_away": m.get("team2", {}).get("teamIconUrl"),
            })
            
        log_info(f"{len(data)} matchs récupérés depuis OpenLigaDB ({shortcut}).", "OPENLIGADB")
        
    return matchs_normalises
