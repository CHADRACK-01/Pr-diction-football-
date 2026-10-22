import pandas as pd
from users.db import get_connection
from core.utils.logs import log_info


def inserer_matchs(liste_matchs):
    """Insère une liste de matchs dans la base Turso."""
    if not liste_matchs:
        return 0

    conn = get_connection()
    inseres = 0
    TAILLE_LOT = 500

    for i in range(0, len(liste_matchs), TAILLE_LOT):
        lot = liste_matchs[i:i + TAILLE_LOT]
        
        # On construit les valeurs pour l'insertion multiple
        valeurs = []
        for m in lot:
            valeurs.append((
                m.get('date'),
                m.get('home_team'),
                m.get('away_team'),
                m.get('fthg'), m.get('ftag'), m.get('ftr'),
                m.get('hthg'), m.get('htag'), m.get('htr'),
                m.get('hs'), m.get('as_shots'), m.get('hst'), m.get('ast'),
                m.get('hc'), m.get('ac'), m.get('hf'), m.get('af'),
                m.get('hy'), m.get('ay'), m.get('hr'), m.get('ar'),
                m.get('b365h'), m.get('b365d'), m.get('b365a'),
                m.get('competition')
            ))
        
        # Construction de la requête avec les placeholders
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
        
        # Exécution pour chaque match (libsql ne supporte pas execute_many directement)
        for vals in valeurs:
            conn.execute(query, vals)
            inseres += 1
        
        conn.commit()
        if (i // TAILLE_LOT) % 10 == 0:
            log_info(f"{inseres} matchs traités...", "MATCHS")

    conn.close()
    log_info(f"{inseres} match(s) traité(s).", "MATCHS")
    return inseres


def charger_tous_les_matchs():
    """Charge tous les matchs depuis Turso dans un DataFrame Pandas."""
    conn = get_connection()
    
    cur = conn.execute("""
        SELECT
            date AS "Date", home_team AS "HomeTeam", away_team AS "AwayTeam",
            fthg AS "FTHG", ftag AS "FTAG", ftr AS "FTR",
            hthg AS "HTHG", htag AS "HTAG", htr AS "HTR",
            hs AS "HS", as_shots AS "AS", hst AS "HST", ast AS "AST",
            hc AS "HC", ac AS "AC", hf AS "HF", af AS "AF",
            hy AS "HY", ay AS "AY", hr AS "HR", ar AS "AR",
            b365h AS "B365H", b365d AS "B365D", b365a AS "B365A",
            competition AS "Competition"
        FROM matchs
        ORDER BY date
    """)
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    conn.close()
    
    df = pd.DataFrame(rows, columns=columns)
    log_info(f"{len(df)} matchs chargés depuis Turso.", "MATCHS")
    return df


def compter_matchs():
    """Compte le nombre total de matchs dans la base."""
    conn = get_connection()
    result = conn.execute("SELECT COUNT(*) FROM matchs").fetchone()
    conn.close()
    return result[0] if result else 0
