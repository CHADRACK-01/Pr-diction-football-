import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import requests
import unicodedata

from core.utils.logs import log_info, log_error, log_warning
from users.db import get_connection, db_execute, db_fetchall
from config import FOOTBALL_DATA_KEY

TZ_KINSHASA = timezone(timedelta(hours=1))

def _normaliser_nom(nom):
    if not nom: return ""
    try:
        nom = unicodedata.normalize('NFKD', nom).encode('ascii', 'ignore').decode('utf-8')
        return nom.lower().replace(" ", "").replace("-", "").strip()
    except: return nom.lower().strip()

def _recuperer_resultats_api(date_str):
    if not FOOTBALL_DATA_KEY: return {}
    try:
        url = f"https://api.football-data.org/v4/matches?dateFrom={date_str}&dateTo={date_str}"
        res = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=15)
        if res.status_code != 200: return {}
        
        resultats = {}
        for m in res.json().get("matches", []):
            if m.get("status") != "FINISHED": continue
            home = m.get("homeTeam", {}).get("name", "")
            away = m.get("awayTeam", {}).get("name", "")
            ft = m.get("score", {}).get("fullTime", {})
            ht = m.get("score", {}).get("halfTime", {})
            
            if ft.get("home") is None: continue
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            resultats[key] = {
                'fthg': ft.get("home"), 'ftag': ft.get("away"),
                'hthg': ht.get("home", 0), 'htag': ht.get("away", 0),
            }
        return resultats
    except Exception as e:
        log_error(f"Erreur API pour {date_str}", "RESULTS", exception=e)
        return {}

def mettre_a_jour_resultats():
    log_info("=== MISE À JOUR DES RÉSULTATS ===", "RESULTS")
    
    # 1. Récupérer les matchs sans score (hier et avant-hier)
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, date, home_team, away_team FROM matchs
        WHERE fthg IS NULL AND date < date('now') AND date > date('now', '-3 days')
    """).fetchall()
    
    matchs_par_date = {}
    for r in rows:
        matchs_par_date.setdefault(r[1], []).append((r[0], r[2], r[3]))

    mises_a_jour = 0
    for date_str, matchs in matchs_par_date.items():
        resultats_api = _recuperer_resultats_api(date_str)
        for match_id, home, away in matchs:
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            if key in resultats_api:
                r = resultats_api[key]
                ftr = 'H' if r['fthg'] > r['ftag'] else 'A' if r['fthg'] < r['ftag'] else 'D'
                conn.execute("""
                    UPDATE matchs SET fthg=?, ftag=?, ftr=?, hthg=?, htag=? WHERE id=?
                """, (r['fthg'], r['ftag'], ftr, r['hthg'], r['htag'], match_id))
                mises_a_jour += 1
    conn.commit()

    # 2. Vérifier les pronostics de la veille
    hier = (datetime.now(TZ_KINSHASA) - timedelta(days=1)).strftime("%Y-%m-%d")
    pronos = db_fetchall("""
        SELECT id, home_team, away_team, pronostic_reco FROM resultats_pronostics
        WHERE date_match = ? AND est_gagnant IS NULL
    """, params=[hier])

    gagnes = 0
    for p in pronos:
        p_id, home, away, reco = p
        # On cherche le match dans la base (qui vient d'être mis à jour)
        match = conn.execute("""
            SELECT fthg, ftag FROM matchs WHERE home_team = ? AND away_team = ? AND date = ?
        """, (home, away, hier)).fetchone()
        
        if match and match[0] is not None:
            sh, sa = match
            est_gagnant = (reco == "1X" and sh >= sa) or (reco == "X2" and sa >= sh) or (reco == "12" and sh != sa)
            if est_gagnant: gagnes += 1
            conn.execute("UPDATE resultats_pronostics SET est_gagnant=? WHERE id=?", (1 if est_gagnant else 0, p_id))
    
    conn.commit()
    conn.close()
    log_info(f"✅ {mises_a_jour} scores mis à jour. {gagnes} pronostics gagnants.", "RESULTS")
