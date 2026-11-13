import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import requests
import unicodedata

from core.utils.logs import log_info, log_error, log_warning
from users.db import get_connection
from config import FOOTBALL_DATA_KEY, BZZOIRO_API_KEY

TZ_KINSHASA = timezone(timedelta(hours=1))

def _get_matchs_sans_resultat():
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT id, date, home_team, away_team, competition
            FROM matchs
            WHERE fthg IS NULL
            AND date < date('now')
            AND date > date('now', '-7 days')
            ORDER BY date DESC
            LIMIT 200
        """)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        log_error("Impossible de récupérer les matchs sans résultat", "MAJ_RESULTATS", exception=e)
        return []

def _normaliser_nom(nom):
    if not nom: return ""
    try:
        nom = unicodedata.normalize('NFKD', nom).encode('ascii', 'ignore').decode('utf-8')
        return nom.lower().replace(" ", "").replace("-", "").strip()
    except Exception:
        return nom.lower().strip()

def _recuperer_resultats_football_data(date_str):
    try:
        url = f"https://api.football-data.org/v4/matches?dateFrom={date_str}&dateTo={date_str}"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code != 200:
            return {}
        
        matchs_api = res.json().get("matches", [])
        resultats = {}
        
        for m in matchs_api:
            if m.get("status") != "FINISHED": continue
            home = m.get("homeTeam", {}).get("name", "")
            away = m.get("awayTeam", {}).get("name", "")
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            ht = score.get("halfTime", {})
            
            if ft.get("home") is None: continue
            
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            resultats[key] = {
                'fthg': ft.get("home"), 'ftag': ft.get("away"),
                'hthg': ht.get("home", 0), 'htag': ht.get("away", 0),
            }
        return resultats
    except Exception as e:
        log_error(f"Football-Data : erreur pour {date_str}", "MAJ_RESULTATS", exception=e)
        return {}

def _calculer_ftr(fthg, ftag):
    if fthg > ftag: return 'H'
    elif fthg < ftag: return 'A'
    else: return 'D'

def mettre_a_jour_resultats():
    log_info("=== DÉBUT DE LA MISE À JOUR DES RÉSULTATS ===", "MAJ_RESULTATS")
    
    matchs_sans_resultat = _get_matchs_sans_resultat()
    if not matchs_sans_resultat:
        log_info("Aucun match à mettre à jour.", "MAJ_RESULTATS")
        return 0
    
    matchs_par_date = {}
    for m in matchs_sans_resultat:
        match_id, date_match, home, away, comp = m
        if date_match not in matchs_par_date:
            matchs_par_date[date_match] = []
        matchs_par_date[date_match].append((match_id, home, away))
    
    tous_resultats = {}
    for date_str in matchs_par_date.keys():
        tous_resultats.update(_recuperer_resultats_football_data(date_str))
    
    conn = get_connection()
    mises_a_jour = 0
    
    for date_match, matchs in matchs_par_date.items():
        for match_id, home, away in matchs:
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            if key not in tous_resultats: continue
            
            score = tous_resultats[key]
            fthg, ftag = score['fthg'], score['ftag']
            hthg, htag = score['hthg'], score['htag']
            ftr = _calculer_ftr(fthg, ftag)
            
            try:
                conn.execute("""
                    UPDATE matchs
                    SET fthg = ?, ftag = ?, ftr = ?, hthg = ?, htag = ?
                    WHERE id = ?
                """, (fthg, ftag, ftr, hthg, htag, match_id))
                mises_a_jour += 1
            except Exception as e:
                log_error(f"Impossible de mettre à jour le match #{match_id}", "MAJ_RESULTATS", exception=e)
    
    conn.commit()
    conn.close()
    log_info(f"=== {mises_a_jour} matchs mis à jour ===", "MAJ_RESULTATS")
    return mises_a_jour

if __name__ == "__main__":
    mettre_a_jour_resultats()
