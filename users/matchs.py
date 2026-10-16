from users.db import get_connection


def inserer_matchs(liste_matchs):
    if not liste_matchs:
        return 0

    try:
        from psycopg2.extras import execute_values

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

        conn = get_connection()
        cur = conn.cursor()

        TAILLE_LOT = 500
        inseres = 0

        for i in range(0, len(valeurs), TAILLE_LOT):
            lot = valeurs[i:i + TAILLE_LOT]
            try:
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
            except Exception as e:
                print(f"⚠️ Erreur lot {i} : {e}")
                conn.rollback()
                continue

        conn.commit()
        cur.close()
        conn.close()
        print(f"💾 {inseres} nouveau(x) match(s) inséré(s).")
        return inseres
    except Exception as e:
        print(f"⚠️ Erreur inserer_matchs : {e}")
        return 0


def charger_tous_les_matchs():
    import pandas as pd
    try:
        conn = get_connection()
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
        conn.close()
        print(f"📥 {len(df)} matchs chargés depuis PostgreSQL.")
        return df
    except Exception as e:
        print(f"⚠️ Erreur charger_tous_les_matchs : {e}")
        import pandas as pd
        return pd.DataFrame()


def compter_matchs():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM matchs")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"⚠️ Erreur compter_matchs : {e}")
        return 0
