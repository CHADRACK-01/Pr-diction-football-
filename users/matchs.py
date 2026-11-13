import json
import requests
from datetime import datetime, timedelta
from config import MAPPING_COMPETITIONS, FOOTBALL_DATA_KEY
from users.db import db_fetchone, db_fetchall, db_execute

CODES_API = {
    "premier_league": "PL", "championship": "ELC", "laliga": "PD", 
    "segunda_division": "SD", "serie_a": "SA", "serie_b": "SB", 
    "ligue_1": "FL1", "ligue_2": "FL2", "bundesliga_1": "BL1", 
    "bundesliga_2": "BL2", "champions_league": "CL",
}

def get_equipes_saison_en_cours(competition):
    if not competition:
        return []

    noms_vers_codes = {v: k for k, v in MAPPING_COMPETITIONS.items()}
    comp_interne = noms_vers_codes.get(competition, competition)
    
    # --- NIVEAU 1 : Base de données locale (Saison en cours) ---
    now = datetime.now()
    annee_debut = now.year if now.month >= 7 else now.year - 1
    saison_str = f"{annee_debut}-{annee_debut+1}"
    
    # On cherche les équipes qui ont des matchs dans la saison actuelle
    comp_clean = comp_interne.lower().replace("_", "").replace(" ", "").replace("-", "")
    rows = db_fetchall(
        """
        SELECT DISTINCT home_team FROM matchs
        WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
          AND saison = ?
        UNION
        SELECT DISTINCT away_team FROM matchs
        WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
          AND saison = ?
        ORDER BY home_team ASC
        """,
        params=[comp_clean, saison_str, comp_clean, saison_str]
    )
    equipes_db = [row[0] for row in rows if row and row[0]]
    
    if equipes_db:
        log_info(f"Niveau 1 (DB) : {len(equipes_db)} équipes pour {competition} ({saison_str})", "MATCHS")
        return sorted(equipes_db)

    # --- NIVEAU 2 : API avec Cache ---
    log_warning(f"Niveau 1 (DB) vide pour {competition}. Passage au Niveau 2 (API).", "MATCHS")
    
    # Vérification du cache
    try:
        cache = db_fetchone("SELECT equipes, date_maj FROM cache_equipes WHERE competition = ?", params=[comp_interne])
        if cache and cache[0] and cache[1]:
            date_maj = datetime.strptime(cache[1], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - date_maj).days < 7:
                log_info(f"Cache API utilisé pour {competition}", "MATCHS")
                return json.loads(cache[0])
    except Exception:
        pass

    # Appel API
    code_api = CODES_API.get(comp_interne)
    if code_api and FOOTBALL_DATA_KEY:
        annee_api = now.year if now.month >= 7 else now.year - 1
        url = f"https://api.football-data.org/v4/competitions/{code_api}/teams?season={annee_api}"
        try:
            res = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=10)
            if res.status_code == 200:
                equipes_api = [team["name"] for team in res.json().get("teams", [])]
                if equipes_api:
                    # Mise en cache
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db_execute(
                        "INSERT OR REPLACE INTO cache_equipes (competition, equipes, date_maj) VALUES (?, ?, ?)",
                        params=[comp_interne, json.dumps(equipes_api), now_str]
                    )
                    log_info(f"Niveau 2 (API) : {len(equipes_api)} équipes pour {competition}", "MATCHS")
                    return sorted(equipes_api)
        except Exception as e:
            log_warning(f"Échec API pour {competition}", "MATCHS", exception=e)

    # --- NIVEAU 3 : Fallback absolu (365 derniers jours) ---
    log_warning(f"Niveau 2 (API) échoué. Passage au Niveau 3 (Fallback).", "MATCHS")
    
    date_limite = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    rows = db_fetchall(
        """
        SELECT DISTINCT home_team FROM matchs
        WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
          AND date >= ?
        UNION
        SELECT DISTINCT away_team FROM matchs
        WHERE (LOWER(REPLACE(REPLACE(REPLACE(TRIM(competition), '_', ''), ' ', ''), '-', '')) = ?) 
          AND date >= ?
        ORDER BY home_team ASC
        """,
        params=[comp_clean, date_limite, comp_clean, date_limite]
    )
    equipes_fallback = [row[0] for row in rows if row and row[0]]
    return sorted(list(set(equipes_fallback)))
