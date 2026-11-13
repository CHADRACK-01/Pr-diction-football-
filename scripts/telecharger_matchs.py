import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
import io
from datetime import datetime

from core.utils.logs import log_info, log_error, log_warning
from users.db import get_connection

DIVS = {
    'E0': 'premier_league', 'E1': 'championship',
    'SP1': 'laliga', 'SP2': 'segunda_division',
    'I1': 'serie_a', 'I2': 'serie_b',
    'F1': 'ligue_1', 'F2': 'ligue_2',
    'D1': 'bundesliga_1', 'D2': 'bundesliga_2',
}

# URL du calendrier complet (mis à jour quotidiennement par football-data.co.uk)
BASE_URL = "https://www.football-data.co.uk/fixtures.csv"

def _inserer_matchs_en_base(all_rows):
    if not all_rows: return 0
    conn = get_connection()
    inseres = 0
    
    query = """
        INSERT OR IGNORE INTO matchs (
            date, home_team, away_team, fthg, ftag, ftr, competition, saison
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    for i in range(0, len(all_rows), 100):
        lot = all_rows[i:i+100]
        for r in lot:
            try:
                conn.execute(query, (
                    r['date'], r['home'], r['away'], 
                    r['fthg'], r['ftag'], r['ftr'], 
                    r['competition'], r['saison']
                ))
                inseres += 1
            except Exception:
                pass
        try: conn.commit()
        except: pass

    conn.close()
    return inseres

def telecharger_tout():
    log_info("=== TÉLÉCHARGEMENT DU CALENDRIER COMPLET ===", "SCRIPTS")
    
    try:
        r = requests.get(BASE_URL, timeout=30)
        if r.status_code != 200:
            log_error(f"HTTP {r.status_code} sur {BASE_URL}", "SCRIPTS")
            return 0

        df = pd.read_csv(io.StringIO(r.text), encoding='cp1252', on_bad_lines='skip')
        
        # Détermination de la saison en cours (ex: "2026-2027")
        now = datetime.now()
        annee_debut = now.year if now.month >= 7 else now.year - 1
        saison_str = f"{annee_debut}-{annee_debut+1}"

        all_rows = []
        for _, row in df.iterrows():
            try:
                div = row.get('Div')
                if div not in DIVS: continue
                
                date_str = pd.to_datetime(row['Date'], format='%d/%m/%Y', errors='coerce')
                if pd.isna(date_str): continue

                fthg = row.get('FTHG')
                ftag = row.get('FTAG')
                
                all_rows.append({
                    'date': date_str.strftime('%Y-%m-%d'),
                    'home': str(row['HomeTeam']).strip(),
                    'away': str(row['AwayTeam']).strip(),
                    'fthg': int(fthg) if pd.notna(fthg) else None,
                    'ftag': int(ftag) if pd.notna(ftag) else None,
                    'ftr': row.get('FTR') if pd.notna(row.get('FTR')) else None,
                    'competition': DIVS[div],
                    'saison': saison_str
                })
            except Exception:
                continue

        inseres = _inserer_matchs_en_base(all_rows)
        log_info(f"✅ {inseres} matchs traités pour la saison {saison_str}", "SCRIPTS")
        return inseres

    except Exception as e:
        log_error("Erreur téléchargement calendrier", "SCRIPTS", exception=e)
        return 0
