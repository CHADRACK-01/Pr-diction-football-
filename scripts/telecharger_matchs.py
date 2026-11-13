import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.logs import log_info, log_error, log_warning
from core.api.orchestrator import collecter_tous_les_matchs
from users.db import get_connection

def _inserer_matchs_en_base(matchs, competition):
    if not matchs: return 0
    conn = get_connection()
    inseres = 0
    erreurs = 0
    
    query = """
        INSERT OR IGNORE INTO matchs (
            date, home_team, away_team, fthg, ftag, ftr,
            hthg, htag, htr, hs, as_shots, hst, ast, hc, ac, hf, af,
            hy, ay, hr, ar, b365h, b365d, b365a, competition
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for i in range(0, len(matchs), 100):
        lot = matchs[i:i+100]
        valeurs = []
        for m in lot:
            date_str = str(m.get('heure', ''))[:10] if m.get('heure') else None
            valeurs.append((
                date_str, m.get('home'), m.get('away'),
                m.get('fthg'), m.get('ftag'), m.get('ftr'),
                m.get('hthg'), m.get('htag'), m.get('htr'),
                None, None, None, None, None, None, None, None, None, None, None, None,
                None, None, None, competition
            ))

        for vals in valeurs:
            try:
                conn.execute(query, vals)
                inseres += 1
            except Exception as e:
                erreurs += 1
        try: conn.commit()
        except: pass

    conn.close()
    if erreurs > 0: log_warning(f"{erreurs} erreurs d'insertion pour {competition}", "SCRIPTS")
    return inseres

def telecharger_tout():
    log_info("=== DÉBUT DU TÉLÉCHARGEMENT ===", "SCRIPTS")
    try:
        matchs = collecter_tous_les_matchs()
    except Exception as e:
        log_error("Erreur orchestrateur", "SCRIPTS", exception=e)
        return 0
    
    if not matchs: return 0

    par_competition = {}
    for m in matchs:
        comp = m.get('competition_reelle', m.get('competition', 'inconnu'))
        par_competition.setdefault(comp, []).append(m)

    total = 0
    for comp, matchs_comp in par_competition.items():
        total += _inserer_matchs_en_base(matchs_comp, comp)
        log_info(f"{comp} : {total} matchs traités.", "SCRIPTS")

    log_info(f"=== FIN TÉLÉCHARGEMENT : {total} matchs ===", "SCRIPTS")
    return total
