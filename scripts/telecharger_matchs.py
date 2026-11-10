import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from core.utils.logs import log_info, log_error, log_warning
from core.api import football_data, bzzoiro, openligadb
from users.db import get_connection

TZ_KINSHASA = timezone(timedelta(hours=1))


def _inserer_matchs_en_base(matchs, competition):
    """Insère une liste de matchs dans Turso (ignore les doublons)."""
    if not matchs:
        return 0

    conn = get_connection()
    inseres = 0
    TAILLE_LOT = 500

    for i in range(0, len(matchs), TAILLE_LOT):
        lot = matchs[i:i + TAILLE_LOT]
        valeurs = []
        
        for m in lot:
            valeurs.append((
                m.get('date'), m.get('home_team'), m.get('away_team'),
                m.get('fthg'), m.get('ftag'), m.get('ftr'),
                m.get('hthg'), m.get('htag'), m.get('htr'),
                m.get('hs'), m.get('as_shots'), m.get('hst'), m.get('ast'),
                m.get('hc'), m.get('ac'), m.get('hf'), m.get('af'),
                m.get('hy'), m.get('ay'), m.get('hr'), m.get('ar'),
                m.get('b365h'), m.get('b365d'), m.get('b365a'),
                competition
            ))

        query = """
            INSERT INTO matchs (
                date, home_team, away_team,
                fthg, ftag, ftr,
                hthg, htag, htr,
                hs, as_shots, hst, ast,
                hc, ac, hf, af,
                hy, ay, hr, ar,
                b365h, b365d, b365a,
                competition
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (date, home_team, away_team, competition) DO NOTHING
        """

        for vals in valeurs:
            try:
                conn.execute(query, vals)
                inseres += 1
            except Exception as e:
                log_error(
                    message=f"Erreur insertion match {vals[1]} vs {vals[2]}",
                    module="SCRIPTS",
                    exception=e
                )

        conn.commit()

    conn.close()
    return inseres


def telecharger_via_football_data():
    """Télécharge les matchs via Football-Data.org."""
    log_info("Début du téléchargement via Football-Data...", "SCRIPTS")
    
    try:
        matchs_bruts = football_data.recuperer_matchs_bruts()
    except Exception as e:
        log_error("Erreur lors de l'appel à Football-Data", "SCRIPTS", exception=e)
        return 0
    
    if not matchs_bruts:
        log_warning("Aucun match récupéré via Football-Data.", "SCRIPTS")
        return 0

    par_competition = {}
    for m in matchs_bruts:
        comp = m.get('competition', 'inconnu')
        if comp not in par_competition:
            par_competition[comp] = []
        par_competition[comp].append({
            'date': m.get('heure', '')[:10] if m.get('heure') else None,
            'home_team': m.get('home'),
            'away_team': m.get('away'),
            'fthg': None, 'ftag': None, 'ftr': None,
            'hthg': None, 'htag': None, 'htr': None,
            'hs': None, 'as_shots': None, 'hst': None, 'ast': None,
            'hc': None, 'ac': None, 'hf': None, 'af': None,
            'hy': None, 'ay': None, 'hr': None, 'ar': None,
            'b365h': None, 'b365d': None, 'b365a': None,
        })

    total = 0
    for comp, matchs in par_competition.items():
        inseres = _inserer_matchs_en_base(matchs, comp)
        log_info(f"Football-Data / {comp} : {inseres} matchs insérés.", "SCRIPTS")
        total += inseres

    return total


def telecharger_via_bzzoiro():
    """Télécharge les matchs via Bzzoiro."""
    log_info("Début du téléchargement via Bzzoiro...", "SCRIPTS")
    
    try:
        matchs_bruts = bzzoiro.get_matchs_du_jour()
    except Exception as e:
        log_error("Erreur lors de l'appel à Bzzoiro", "SCRIPTS", exception=e)
        return 0
    
    if not matchs_bruts:
        log_warning("Aucun match récupéré via Bzzoiro.", "SCRIPTS")
        return 0

    par_competition = {}
    for m in matchs_bruts:
        comp = m.get('competition', 'inconnu')
        if comp not in par_competition:
            par_competition[comp] = []
        par_competition[comp].append({
            'date': m.get('heure', '')[:10] if m.get('heure') else None,
            'home_team': m.get('home'),
            'away_team': m.get('away'),
            'fthg': None, 'ftag': None, 'ftr': None,
            'hthg': None, 'htag': None, 'htr': None,
            'hs': None, 'as_shots': None, 'hst': None, 'ast': None,
            'hc': None, 'ac': None, 'hf': None, 'af': None,
            'hy': None, 'ay': None, 'hr': None, 'ar': None,
            'b365h': None, 'b365d': None, 'b365a': None,
        })

    total = 0
    for comp, matchs in par_competition.items():
        inseres = _inserer_matchs_en_base(matchs, comp)
        log_info(f"Bzzoiro / {comp} : {inseres} matchs insérés.", "SCRIPTS")
        total += inseres

    return total


def telecharger_via_openligadb():
    """Télécharge les matchs via OpenLigaDB."""
    log_info("Début du téléchargement via OpenLigaDB...", "SCRIPTS")
    
    try:
        matchs_bruts = openligadb.get_matchs_du_jour()
    except Exception as e:
        log_error("Erreur lors de l'appel à OpenLigaDB", "SCRIPTS", exception=e)
        return 0
    
    if not matchs_bruts:
        log_warning("Aucun match récupéré via OpenLigaDB.", "SCRIPTS")
        return 0

    par_competition = {}
    for m in matchs_bruts:
        comp = m.get('competition', 'inconnu')
        if comp not in par_competition:
            par_competition[comp] = []
        par_competition[comp].append({
            'date': m.get('heure', '')[:10] if m.get('heure') else None,
            'home_team': m.get('home'),
            'away_team': m.get('away'),
            'fthg': None, 'ftag': None, 'ftr': None,
            'hthg': None, 'htag': None, 'htr': None,
            'hs': None, 'as_shots': None, 'hst': None, 'ast': None,
            'hc': None, 'ac': None, 'hf': None, 'af': None,
            'hy': None, 'ay': None, 'hr': None, 'ar': None,
            'b365h': None, 'b365d': None, 'b365a': None,
        })

    total = 0
    for comp, matchs in par_competition.items():
        inseres = _inserer_matchs_en_base(matchs, comp)
        log_info(f"OpenLigaDB / {comp} : {inseres} matchs insérés.", "SCRIPTS")
        total += inseres

    return total


def telecharger_tout():
    """Télécharge les matchs de toutes les sources disponibles."""
    log_info("=== DÉBUT DU TÉLÉCHARGEMENT AUTOMATIQUE ===", "SCRIPTS")
    
    total_fd = telecharger_via_football_data()
    total_bz = telecharger_via_bzzoiro()
    total_ol = telecharger_via_openligadb()
    
    total = total_fd + total_bz + total_ol
    
    if total > 0:
        log_info(f"=== FIN DU TÉLÉCHARGEMENT : {total} matchs traités ===", "SCRIPTS")
    else:
        log_warning("=== FIN DU TÉLÉCHARGEMENT : aucun match récupéré ===", "SCRIPTS")
    
    return total


if __name__ == "__main__":
    telecharger_tout()
