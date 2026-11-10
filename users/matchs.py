from users.db import get_connection
from core.utils.logs import log_info, log_error


def inserer_matchs(liste_matchs):
    """Insère une liste de matchs dans la base Turso."""
    if not liste_matchs:
        return 0

    conn = get_connection()
    inseres = 0
    TAILLE_LOT = 500

    for i in range(0, len(liste_matchs), TAILLE_LOT):
        lot = liste_matchs[i:i + TAILLE_LOT]
        
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
                m.get('competition')
            ))
        
        placeholders = ", ".join(["?"] * 25)
        query = f"""
            INSERT INTO matchs (
                date, home_team, away_team,
                fthg, ftag, ftr,
                hthg, htag, htr,
                hs, as_shots, hst, ast,
                hc, ac, hf, af,
                hy, ay, hr, ar,
                b365h, b365d, b365a,
                competition
            ) VALUES ({placeholders})
            ON CONFLICT (date, home_team, away_team, competition) DO NOTHING
        """
        
        for vals in valeurs:
            try:
                conn.execute(query, vals)
                inseres += 1
            except Exception as e:
                log_error("Erreur lors de l'insertion d'un match", "MATCHS", exception=e)
        
        conn.commit()
        if (i // TAILLE_LOT) % 10 == 0:
            log_info(f"{inseres} matchs traités...", "MATCHS")

    conn.close()
    log_info(f"{inseres} match(s) traité(s).", "MATCHS")
    return inseres


def compter_matchs():
    """Compte le nombre total de matchs dans la base."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM matchs").fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error("Impossible de compter les matchs", "MATCHS", exception=e)
        return 0
