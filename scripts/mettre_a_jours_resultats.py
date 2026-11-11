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
    """Récupère les matchs passés qui n'ont pas encore de score."""
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
    """Normalise un nom pour le matching (accents, casse, espaces)."""
    if not nom:
        return ""
    try:
        nom = unicodedata.normalize('NFKD', nom).encode('ascii', 'ignore').decode('utf-8')
        return nom.lower().replace(" ", "").replace("-", "").strip()
    except Exception as e:
        log_warning(f"Impossible de normaliser '{nom}' : {e}", "MAJ_RESULTATS")
        return nom.lower().strip()


def _recuperer_resultats_football_data(date_str):
    """Récupère les résultats d'une date via Football-Data."""
    try:
        url = f"https://api.football-data.org/v4/matches?dateFrom={date_str}&dateTo={date_str}"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        res = requests.get(url, headers=headers, timeout=15)
        
        # Gestion des erreurs HTTP
        if res.status_code == 400:
            # Pas de match pour cette date, c'est normal
            log_info(f"Football-Data / {date_str} : aucun match (400).", "MAJ_RESULTATS")
            return {}
        elif res.status_code == 403:
            log_error("Football-Data : accès refusé (clé invalide)", "MAJ_RESULTATS")
            return {}
        elif res.status_code == 429:
            log_error("Football-Data : quota dépassé (429)", "MAJ_RESULTATS")
            return {}
        elif res.status_code != 200:
            log_error(f"Football-Data : erreur {res.status_code} pour {date_str}", "MAJ_RESULTATS")
            return {}
        
        matchs_api = res.json().get("matches", [])
        resultats = {}
        
        for m in matchs_api:
            if m.get("status") != "FINISHED":
                continue
            
            home = m.get("homeTeam", {}).get("name", "")
            away = m.get("awayTeam", {}).get("name", "")
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            ht = score.get("halfTime", {})
            
            if ft.get("home") is None or ft.get("away") is None:
                continue
            
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            resultats[key] = {
                'fthg': ft.get("home"),
                'ftag': ft.get("away"),
                'hthg': ht.get("home", 0) or 0,
                'htag': ht.get("away", 0) or 0,
                'hs': None, 'as_shots': None, 'hst': None, 'ast': None,
                'hc': None, 'ac': None, 'hf': None, 'af': None,
                'hy': None, 'ay': None, 'hr': None, 'ar': None,
                'b365h': None, 'b365d': None, 'b365a': None,
            }
        
        return resultats
    except requests.exceptions.Timeout:
        log_error(f"Football-Data : timeout pour {date_str}", "MAJ_RESULTATS")
        return {}
    except Exception as e:
        log_error(f"Football-Data : erreur pour {date_str}", "MAJ_RESULTATS", exception=e)
        return {}


def _recuperer_resultats_bzzoiro():
    """Récupère les résultats récents via Bzzoiro."""
    try:
        url = "https://sports.bzzoiro.com/api/v2/events/live/"
        headers = {"Authorization": f"Token {BZZOIRO_API_KEY}"}
        res = requests.get(url, headers=headers, params={"sport": "football"}, timeout=15)
        
        if res.status_code != 200:
            log_error(f"Bzzoiro : erreur {res.status_code}", "MAJ_RESULTATS")
            return {}
        
        data = res.json()
        matchs = data.get("results", data) if isinstance(data, dict) else data
        
        resultats = {}
        for m in matchs:
            if not isinstance(m, dict):
                continue
            
            status = m.get("status", "")
            if status not in ["finished", "FT", "full_time"]:
                continue
            
            home = m.get("home_team")
            if isinstance(home, dict):
                home = home.get("name")
            away = m.get("away_team")
            if isinstance(away, dict):
                away = away.get("name")
            
            score_home = m.get("home_score")
            score_away = m.get("away_score")
            
            if not home or not away or score_home is None or score_away is None:
                continue
            
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            
            stats = m.get("stats", {}) or {}
            
            resultats[key] = {
                'fthg': int(score_home),
                'ftag': int(score_away),
                'hthg': int(m.get("home_score_ht", 0) or 0),
                'htag': int(m.get("away_score_ht", 0) or 0),
                'hs': stats.get("home_shots"),
                'as_shots': stats.get("away_shots"),
                'hst': stats.get("home_shots_on_target"),
                'ast': stats.get("away_shots_on_target"),
                'hc': stats.get("home_corners"),
                'ac': stats.get("away_corners"),
                'hf': stats.get("home_fouls"),
                'af': stats.get("away_fouls"),
                'hy': stats.get("home_yellow_cards"),
                'ay': stats.get("away_yellow_cards"),
                'hr': stats.get("home_red_cards"),
                'ar': stats.get("away_red_cards"),
                'b365h': None, 'b365d': None, 'b365a': None,
            }
        
        return resultats
    except Exception as e:
        log_error("Bzzoiro : erreur récupération résultats", "MAJ_RESULTATS", exception=e)
        return {}


def _calculer_ftr(fthg, ftag):
    if fthg > ftag: return 'H'
    elif fthg < ftag: return 'A'
    else: return 'D'


def _calculer_htr(hthg, htag):
    if hthg > htag: return 'H'
    elif hthg < htag: return 'A'
    else: return 'N'


def mettre_a_jour_resultats():
    """
    Met à jour TOUTES les colonnes de résultats des matchs passés.
    """
    log_info("=== DÉBUT DE LA MISE À JOUR DES RÉSULTATS ===", "MAJ_RESULTATS")
    
    matchs_sans_resultat = _get_matchs_sans_resultat()
    if not matchs_sans_resultat:
        log_info("Aucun match à mettre à jour.", "MAJ_RESULTATS")
        return 0
    
    log_info(f"{len(matchs_sans_resultat)} matchs à mettre à jour.", "MAJ_RESULTATS")
    
    matchs_par_date = {}
    for m in matchs_sans_resultat:
        match_id, date_match, home, away, comp = m
        if date_match not in matchs_par_date:
            matchs_par_date[date_match] = []
        matchs_par_date[date_match].append((match_id, home, away, comp))
    
    tous_resultats = {}
    
    # 1. Football-Data
    for date_str in matchs_par_date.keys():
        resultats_fd = _recuperer_resultats_football_data(date_str)
        tous_resultats.update(resultats_fd)
        log_info(f"Football-Data / {date_str} : {len(resultats_fd)} résultats.", "MAJ_RESULTATS")
    
    # 2. Bzzoiro
    resultats_bz = _recuperer_resultats_bzzoiro()
    tous_resultats.update(resultats_bz)
    log_info(f"Bzzoiro : {len(resultats_bz)} résultats.", "MAJ_RESULTATS")
    
    # Mise à jour en base
    conn = get_connection()
    mises_a_jour = 0
    
    for date_match, matchs in matchs_par_date.items():
        for match_id, home, away, comp in matchs:
            key = f"{_normaliser_nom(home)}_{_normaliser_nom(away)}"
            
            if key not in tous_resultats:
                continue
            
            score = tous_resultats[key]
            fthg = score['fthg']
            ftag = score['ftag']
            hthg = score['hthg']
            htag = score['htag']
            
            ftr = _calculer_ftr(fthg, ftag)
            htr = _calculer_htr(hthg, htag)
            
            try:
                conn.execute("""
                    UPDATE matchs
                    SET fthg = ?, ftag = ?, ftr = ?,
                        hthg = ?, htag = ?, htr = ?,
                        hs = ?, as_shots = ?, hst = ?, ast = ?,
                        hc = ?, ac = ?, hf = ?, af = ?,
                        hy = ?, ay = ?, hr = ?, ar = ?,
                        b365h = ?, b365d = ?, b365a = ?
                    WHERE id = ?
                """, (
                    fthg, ftag, ftr,
                    hthg, htag, htr,
                    score.get('hs'), score.get('as_shots'),
                    score.get('hst'), score.get('ast'),
                    score.get('hc'), score.get('ac'),
                    score.get('hf'), score.get('af'),
                    score.get('hy'), score.get('ay'),
                    score.get('hr'), score.get('ar'),
                    score.get('b365h'), score.get('b365d'), score.get('b365a'),
                    match_id
                ))
                mises_a_jour += 1
            except Exception as e:
                log_error(f"Impossible de mettre à jour le match #{match_id}", "MAJ_RESULTATS", exception=e)
    
    conn.commit()
    conn.close()
    
    log_info(f"=== {mises_a_jour} matchs mis à jour sur {len(matchs_sans_resultat)} ===", "MAJ_RESULTATS")
    return mises_a_jour


if __name__ == "__main__":
    mettre_a_jour_resultats()
