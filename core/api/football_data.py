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
    Retourne True si on peut continuer, False sinon.
    """
    if status_code == 200:
        return True
    
    if status_code == 403:
        log_error(f"Accès refusé à l'API Football-Data ({competition}). Vérifie ta clé API.", "API")
        return False
    elif status_code == 400:
        # Erreur 400 : généralement "pas de match pour cette date" → pas grave
        return True
    elif status_code == 404:
        return True
    elif status_code == 429:
        log_error("Quota API Football-Data dépassé (429). Pause nécessaire.", "API")
        return False
    elif status_code == 500:
        log_error("Erreur interne du serveur Football-Data (500).", "API")
        return False
    elif status_code >= 400:
        # On ne loggue plus chaque erreur individuellement
        return False
    
    return True


def recuperer_matchs_bruts():
    """
    Récupère les matchs des 3 prochains jours depuis l'API Football-Data.org.
    """
    log_info("Début de la récupération des matchs depuis Football-Data.org...", "API")
    
    if not FOOTBALL_DATA_KEY:
        log_error("Clé API Football-Data manquante (FOOTBALL_DATA_KEY vide)", "API")
        return []
    
    date_debut = datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")
    date_fin = (datetime.now(TZ_KINSHASA) + timedelta(days=3)).strftime("%Y-%m-%d")
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    matchs_bruts = []
    erreurs_graves = 0
    competitions_vides = 0

    for code, comp_code in COMPETITIONS.items():
        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"dateFrom": date_debut, "dateTo": date_fin}
            
            res = requests.get(url, headers=headers, params=params, timeout=15)
            
            # Gestion simplifiée
            if res.status_code == 200:
                data = res.json()
                matchs_comp = data.get("matches", [])
                count_comp = 0
                
                for m in matchs_comp:
                    status = m.get("status", "")
                    if status not in ["SCHEDULED", "TIMED"]: 
                        continue

                    home_team = m.get("homeTeam", {}) or {}
                    away_team = m.get("awayTeam", {}) or {}
                    home_name = home_team.get("name")
                    away_name = away_team.get("name")
                    
                    if not home_name or not away_name:
                        continue

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

                    matchs_bruts.append({
                        "competition": code,
                        "heure": m.get("utcDate"),
                        "home": home_name,
                        "away": away_name,
                        "cotes_book": cotes_book
                    })
                    count_comp += 1
                
                if count_comp > 0:
                    log_info(f"Football-Data / {code} : {count_comp} matchs récupérés.", "API")
            elif res.status_code == 400:
                # Pas de match pour cette compétition, c'est normal
                competitions_vides += 1
            elif res.status_code == 403:
                log_error(f"Football-Data : accès refusé (clé API invalide)", "API")
                erreurs_graves += 1
            elif res.status_code == 429:
                log_error("Football-Data : quota dépassé (429)", "API")
                erreurs_graves += 1
            else:
                erreurs_graves += 1
            
            # Pause pour respecter la limite
            time.sleep(1)
                
        except requests.exceptions.Timeout:
            erreurs_graves += 1
        except requests.exceptions.ConnectionError:
            erreurs_graves += 1
        except Exception as e:
            log_error(f"Exception inattendue pour {code}", "API", exception=e)
            erreurs_graves += 1
            continue

    # Bilan final (un seul message, pas 7)
    if erreurs_graves > 0 and len(matchs_bruts) == 0:
        log_error(
            f"Football-Data : toutes les compétitions ont échoué ({erreurs_graves} erreurs graves).",
            "API"
        )
    elif len(matchs_bruts) > 0:
        log_info(
            f"Football-Data : {len(matchs_bruts)} matchs récupérés au total.",
            "API"
        )
    else:
        log_info(
            f"Football-Data : aucun match trouvé ({competitions_vides} compétitions sans match).",
            "API"
        )
    
    return matchs_bruts
