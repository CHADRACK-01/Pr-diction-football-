import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.logs import log_info, log_error, log_warning
from core.api.orchestrator import collecter_tous_les_matchs
from users.db import get_connection


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


def telecharger_tout():
    """Télécharge les matchs via l'orchestrateur multi-sources."""
    log_info("=== DÉBUT DU TÉLÉCHARGEMENT AUTOMATIQUE ===", "SCRIPTS")
    
    try:
        matchs = collecter_tous_les_matchs()
    except Exception as e:
        log_error("Erreur lors de l'appel à l'orchestrateur", "SCRIPTS", exception=e)
        return 0
    
    if not matchs:
        log_warning("Aucun match récupéré par l'orchestrateur.", "SCRIPTS")
        return 0

    # On regroupe par compétition
    par_competition = {}
    for m in matchs:
        comp = m.get('competition', 'inconnu')
        if comp not in par_competition:
            par_competition[comp] = []
        
        # On normalise le format pour l'insertion
        par_competition[comp].append({
            'date': m.get('heure', '')[:10] if m.get('heure') else None,
            'home_team': m.get('home'),
            'away_team': m.get('away'),
            'fthg': m.get('fthg'), 'ftag': m.get('ftag'), 'ftr': m.get('ftr'),
            'hthg': m.get('hthg'), 'htag': m.get('htag'), 'htr': m.get('htr'),
            'hs': m.get('hs'), 'as_shots': m.get('as_shots'),
            'hst': m.get('hst'), 'ast': m.get('ast'),
            'hc': m.get('hc'), 'ac': m.get('ac'),
            'hf': m.get('hf'), 'af': m.get('af'),
            'hy': m.get('hy'), 'ay': m.get('ay'),
            'hr': m.get('hr'), 'ar': m.get('ar'),
            'b365h': m.get('b365h'), 'b365d': m.get('b365d'), 'b365a': m.get('b365a'),
        })

    total = 0
    for comp, matchs_comp in par_competition.items():
        inseres = _inserer_matchs_en_base(matchs_comp, comp)
        log_info(f"{comp} : {inseres} matchs insérés.", "SCRIPTS")
        total += inseres

    log_info(f"=== FIN DU TÉLÉCHARGEMENT : {total} matchs traités ===", "SCRIPTS")
    return total


if __name__ == "__main__":
    telecharger_tout()
