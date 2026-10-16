def inserer_matchs(liste_matchs):
    """Insère une liste de matchs enrichis dans PostgreSQL (par lots)."""
    if not liste_matchs:
        return 0

    try:
        from psycopg2.extras import execute_values

        # Préparer les tuples
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

        # Insérer par lots de 500
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
