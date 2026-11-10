import time
import requests
from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error, log_warning
from config import FOOTBALL_DATA_KEY

TZ_KINSHASA = timezone(timedelta(hours=1))

# Liste des compétitions supportées par Football-Data.org
COMPETITIONS = {
    "premier_league": "PL",
    "championship": "ELC",
    "laliga": "PD",
    "ligue_1": "FL1",
    "bundesliga_1": "BL1",
    "serie_a": "SA",
    "champions_league": "CL",
}


def _gerer_erreur_http(status_code, competition):
    """
    Gère les erreurs HTTP de l'API Football-Data.
    Retourne True si on peut continuer pour les autres compétitions, False sinon.
    """
    if status_code == 200:
        return True
    
    if status_code == 403:
        log_error(f"Accès refusé à l'API Football-Data ({competition}). Vérifie ta clé API.", "API")
        return False
    elif status_code == 404:
        # Pas de match pour cette compétition : c'est normal
        log_warning(f"Aucun match trouvé pour {competition} (404).", "API")
        return True
    elif status_code == 429:
        log_error("Quota API Football-Data dépassé (429). Pause nécessaire.", "API")
        return False
    elif status_code == 500:
        log_error("Erreur interne du serveur Football-Data (500).", "API")
        return False
    elif status_code >= 400:
        log_error(f"Erreur API Football-Data ({status_code}) pour {competition}.", "API")
        return False
    
    return True


def recuperer_matchs_bruts():
    """
    Récupère les matchs des 3 prochains jours depuis l'API Football-Data.org.
    Retourne une liste de dictionnaires bruts (sans prédiction).
    """
    log_info("Début de la récupération des matchs depuis Football-Data.org...", "API")
    
    if not FOOTBALL_DATA_KEY:
        log_error("Clé API Football-Data manquante (FOOTBALL_DATA_KEY vide)", "API")
        return []
    
    date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=3)).strftime("%Y-%m-%d")
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matchs_bruts = []
    competitions_reussies = 0
    competitions_echouees = 0

    for code, comp_code in COMPETITIONS.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"dateFrom": date_debut, "dateTo": date_fin}
            
            res = requests.get(url, headers=headers, params=params, timeout=15)
            
            # Gestion des erreurs HTTP
            if not _gerer_erreur_http(res.status_code, code):
                competitions_echouees += 1
                continue
                
            if res.status_code == 404:
                continue  # Pas de match pour cette compétition
            
            data = res.json()
            matchs_comp = data.get("matches", [])
            count_comp = 0
            
            for m in matchs_comp:
                status = m.get("status", "")
                if status not in ["SCHEDULED", "TIMED"]: 
                    continue

                # Extraction sécurisée des équipes
                home_team = m.get("homeTeam", {}) or {}
                away_team = m.get("awayTeam", {}) or {}
                home_name = home_team.get("name")
                away_name = away_team.get("name")
                
                if not home_name or not away_name:
                    log_warning(f"Match sans nom d'équipe ignoré ({code})", "API")
                    continue

                # Extraction sécurisée des cotes
                cotes_book = None
                odds = m.get("odds", {})
                if isinstance(odds, dict) and "bet365" in odds:
                    b365 = odds["bet365"]
                    if b365 and b365.get('homeWin') and b365.get('draw') and b365.get('awayWin'):
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
                    "heure": m.get("utcDate"),
                    "home": home_name,
                    "away": away_name,
                    "cotes_book": cotes_book
                })
                count_comp += 1
            
            competitions_reussies += 1
            if count_comp > 0:
                log_info(f"Football-Data / {code} : {count_comp} matchs récupérés.", "API")
            
            # Pause pour respecter la limite (10 requêtes/minute)
            time.sleep(1)
                
        except requests.exceptions.Timeout:
            log_error(f"Timeout de l'API Football-Data pour {code}", "API")
            competitions_echouees += 1
        except requests.exceptions.ConnectionError as e:
            log_error(f"Erreur de connexion Football-Data pour {code}", "API", exception=e)
            competitions_echouees += 1
        except Exception as e:
            log_error(f"Exception inattendue pour {code}", "API", exception=e)
            competitions_echouees += 1
            continue

    # Bilan final
    if competitions_reussies == 0 and competitions_echouees > 0:
        log_error(
            f"Football-Data : AUCUNE compétition n'a répondu "
            f"({competitions_echouees} échecs). L'API est probablement HS.",
            "API"
        )
    else:
        log_info(
            f"Football-Data : {len(matchs_bruts)} matchs bruts récupérés "
            f"({competitions_reussies} compétitions OK, {competitions_echouees} échecs).",
            "API"
        )
    
    return matchs_bruts
