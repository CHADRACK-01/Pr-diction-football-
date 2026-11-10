import requests
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://api.openligadb.de"
TZ_KINSHASA = timezone(timedelta(hours=1))

# Mapping des noms de ligues OpenLigaDB vers nos codes internes
LIGUES_OPENLIGADB = {
    "bl1": "bundesliga_1",
    "bl2": "bundesliga_2",
}


def tester_api():
    """Vérifie si l'API OpenLigaDB répond."""
    try:
        res = requests.get(f"{BASE_URL}/getavailableleagues", timeout=10)
        if res.status_code == 200:
            log_info("API OpenLigaDB : OK", "OPENLIGADB")
            return True
        else:
            log_warning(f"API OpenLigaDB : Statut {res.status_code}", "OPENLIGADB")
            return False
    except requests.exceptions.Timeout:
        log_error("API OpenLigaDB : timeout lors du test", "OPENLIGADB")
        return False
    except requests.exceptions.ConnectionError as e:
        log_error("API OpenLigaDB : impossible de se connecter", "OPENLIGADB", exception=e)
        return False
    except Exception as e:
        log_error("API OpenLigaDB : erreur inattendue lors du test", "OPENLIGADB", exception=e)
        return False


def get_matchs_du_jour():
    """
    Récupère les matchs de Bundesliga (bl1) et 2. Bundesliga (bl2) 
    pour la journée en cours.
    """
    matchs_normalises = []
    ligues_reussies = 0
    ligues_echouees = 0
    
    now = datetime.now(TZ_KINSHASA)
    saison = now.year if now.month >= 7 else now.year - 1
    
    for shortcut, comp_code in LIGUES_OPENLIGADB.items():
        try:
            # On récupère les matchs de la journée 1 (approximation)
            url = f"{BASE_URL}/getmatchdata/{shortcut}/{saison}/1"
            res = requests.get(url, timeout=15)
            
            # Gestion des erreurs HTTP
            if res.status_code == 404:
                log_warning(f"OpenLigaDB : pas de données pour {shortcut} (404)", "OPENLIGADB")
                continue
            elif res.status_code == 500:
                log_error(f"OpenLigaDB : erreur serveur pour {shortcut} (500)", "OPENLIGADB")
                ligues_echouees += 1
                continue
            elif res.status_code != 200:
                log_error(f"OpenLigaDB : erreur {res.status_code} pour {shortcut}", "OPENLIGADB")
                ligues_echouees += 1
                continue
                
            data = res.json()
            if not isinstance(data, list):
                log_warning(f"OpenLigaDB : format inattendu pour {shortcut}", "OPENLIGADB")
                continue
            
            count_ligue = 0
            for m in data:
                if not isinstance(m, dict):
                    continue
                
                # On ne garde que les matchs qui ne sont pas encore joués
                if m.get("matchIsFinished"):
                    continue
                
                # Extraction sécurisée des équipes
                team1 = m.get("team1") or {}
                team2 = m.get("team2") or {}
                
                if not isinstance(team1, dict) or not isinstance(team2, dict):
                    continue
                
                home = team1.get("teamName")
                away = team2.get("teamName")
                
                if not home or not away:
                    continue
                
                # Extraction de l'heure
                heure = m.get("matchDateTimeUTC")
                if not heure:
                    continue
                
                matchs_normalises.append({
                    "competition": comp_code,
                    "heure": heure,
                    "home": home,
                    "away": away,
                    "cotes_book": None,  # OpenLigaDB ne fournit pas de cotes
                    "logo_home": team1.get("teamIconUrl"),
                    "logo_away": team2.get("teamIconUrl"),
                })
                count_ligue += 1
            
            ligues_reussies += 1
            log_info(f"OpenLigaDB / {shortcut} : {count_ligue} matchs récupérés.", "OPENLIGADB")
            
        except requests.exceptions.Timeout:
            log_error(f"OpenLigaDB : timeout pour {shortcut}", "OPENLIGADB")
            ligues_echouees += 1
        except requests.exceptions.ConnectionError as e:
            log_error(f"OpenLigaDB : erreur de connexion pour {shortcut}", "OPENLIGADB", exception=e)
            ligues_echouees += 1
        except Exception as e:
            log_error(f"OpenLigaDB : erreur inattendue pour {shortcut}", "OPENLIGADB", exception=e)
            ligues_echouees += 1
            continue

    # Bilan final
    if ligues_reussies == 0 and ligues_echouees > 0:
        log_error(
            f"OpenLigaDB : AUCUNE ligue n'a répondu ({ligues_echouees} échecs). "
            "L'API est probablement HS.",
            "OPENLIGADB"
        )
    else:
        log_info(
            f"OpenLigaDB : {len(matchs_normalises)} matchs au total "
            f"({ligues_reussies} ligues OK, {ligues_echouees} échecs).",
            "OPENLIGADB"
        )
            
    return matchs_normalises
