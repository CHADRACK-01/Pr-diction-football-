import requests
from core.utils.logs import log_info, log_error

BASE_URL = "https://api.openligadb.de"

def tester_api():
    """Vérifie si l'API OpenLigaDB répond."""
    try:
        res = requests.get(f"{BASE_URL}/getavailableleagues", timeout=10)
        return res.status_code == 200
    except Exception:
        return False

def get_matchs_bundesliga(season: str, matchday: int):
    """
    Récupère les matchs de la Bundesliga pour une saison et une journée.
    Exemple : season="2023", matchday=1
    """
    try:
        url = f"{BASE_URL}/getmatchdata/bl1/{season}/{matchday}"
        res = requests.get(url, timeout=15)
        if res.status_code != 200:
            log_error(f"OpenLigaDB Error {res.status_code}", "OPENLIGADB")
            return []
        return res.json()
    except Exception as e:
        log_error(f"Erreur OpenLigaDB : {e}", "OPENLIGADB", e)
        return []
