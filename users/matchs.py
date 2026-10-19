import pandas as pd
from psycopg2.extras import execute_values
from users.db import get_connection
from core.utils.logs import log_info


def inserer_matchs(liste_matchs):
    if not liste_matchs:
        return 0

    valeurs = []
    for m in liste_matchs:
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

    inseres = 0
    TAILLE_LOT = 500

    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(valeurs), TAILLE_LOT):
                lot = valeurs[i:i + TAILLE_LOT]
                execute_values(cur, """
                    INSERT INTO matchs (
                        date, home_team, away_team,
                        fthg, ftag, ftr,
                        hthg, htag, htr,
                        hs, as_shots, hst, ast,
                        hc, ac, hf, af,
                        hy, ay, hr, ar,
                        b365h, b365d, b365a,
                        competition
                    ) VALUES %s
                    ON CONFLICT (date, home_team, away_team, competition) DO NOTHING
                """, lot)
                inseres += cur.rowcount
        conn.commit()
        
    log_info(f"{inseres} nouveau(x) match(s) inséré(s).", "MATCHS")
    return inseres


def charger_tous_les_matchs():
    with get_connection() as conn:
        query = """
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
        """
        df = pd.read_sql(query, conn)
        
    log_info(f"{len(df)} matchs chargés depuis PostgreSQL.", "MATCHS")
    return df


def compter_matchs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM matchs")
            result = cur.fetchone()
            return result[0] if result else 0
