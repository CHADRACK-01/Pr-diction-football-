import requests
from datetime import datetime, timedelta, timezone
from core.utils.logs import log_info, log_error, log_warning
from core.api.api_errors import gerer_erreur_api

FOOTBALL_DATA_KEY = "5a7a6a3afcca4bc88400d73a0e394588"
TZ_KINSHASA = timezone(timedelta(hours=1))

# Liste des compétitions supportées
COMPETITIONS = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "ligue_1": "FL1",
    "bundesliga_1": "BL1",
    "serie_a": "SA",
}

def recuperer_matchs_bruts():
    """
    Récupère les matchs des 3 prochains jours depuis l'API.
    Retourne une liste de dictionnaires bruts (sans prédiction).
    """
    log_info("Début de la récupération des matchs depuis l'API...", "API")
    
    date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=3)).strftime("%Y-%m-%d")
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matchs_bruts = []

    for code, comp_code in COMPETITIONS.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"dateFrom": date_debut, "dateTo": date_fin}
            
            res = requests.get(url, headers=headers, params=params, timeout=15)
            
            # Gestion centralisée de l'erreur
            if not gerer_erreur_api(res.status_code, code):
                continue
                
            data = res.json()
            for m in data.get("matches", []):
                status = m.get("status", "")
                if status not in ["SCHEDULED", "TIMED"]: 
                    continue

                # Extraction des cotes Bet365 si disponibles
                cotes_book = None
                odds = m.get("odds", {})
                if isinstance(odds, dict) and "bet365" in odds:
                    b365 = odds["bet365"]
                    cotes_book = {
                        'h': b365.get('homeWin'),
                        'd': b365.get('draw'),
                        'a': b365.get('awayWin')
                    }
                elif isinstance(odds, dict) and odds.get('homeWin'):
                    cotes_book = {
                        'h': odds.get('homeWin'),
                        'd': odds.get('draw'),
                        'a': odds.get('awayWin')
                    }

                matchs_bruts.append({
                    "competition": code,
                    "heure": m["utcDate"],
                    "home": m["homeTeam"]["name"],
                    "away": m["awayTeam"]["name"],
                    "cotes_book": cotes_book
                })
                
        except requests.exceptions.Timeout:
            log_error(f"Timeout de l'API pour {code}", "API")
        except requests.exceptions.ConnectionError:
            log_error(f"Erreur de connexion pour {code}", "API")
        except Exception as e:
            log_error(f"Exception inattendue pour {code}: {e}", "API")
            continue

    log_info(f"{len(matchs_bruts)} matchs bruts récupérés au total.", "API")
    return matchs_bruts
