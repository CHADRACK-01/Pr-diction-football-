import os
import psycopg2
import psycopg2.extras
from datetime import datetime

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
)


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME, sslmode="require"
    )


# =========================================================
# INITIALISATION DES TABLES
# =========================================================
def initialiser_tables():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                status TEXT DEFAULT 'free',
                date_inscription TIMESTAMP DEFAULT NOW(),
                date_expiration TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS compteurs_jour (
                user_id BIGINT,
                date DATE,
                compteur INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS matchs (
                id SERIAL PRIMARY KEY,
                date DATE,
                home_team TEXT,
                away_team TEXT,
                fthg INTEGER,
                ftag INTEGER,
                ftr TEXT,
                hthg INTEGER,
                htag INTEGER,
                htr TEXT,
                hs INTEGER,
                as_shots INTEGER,
                hst INTEGER,
                ast INTEGER,
                hc INTEGER,
                ac INTEGER,
                hf INTEGER,
                af INTEGER,
                hy INTEGER,
                ay INTEGER,
                hr INTEGER,
                ar INTEGER,
                b365h REAL,
                b365d REAL,
                b365a REAL,
                competition TEXT,
                UNIQUE(date, home_team, away_team, competition)
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_matchs_date ON matchs(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_matchs_home ON matchs(home_team)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_matchs_away ON matchs(away_team)")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tables PostgreSQL prêtes (avec colonnes enrichies).")
    except Exception as e:
        print(f"❌ Erreur init tables : {e}")


# =========================================================
# MATCHS
# =========================================================
def inserer_matchs(liste_matchs):
    """Insère une liste de matchs enrichis dans PostgreSQL (par lots)."""
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


# =========================================================
# UTILISATEURS
# =========================================================
def utilisateur_existe(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM utilisateurs WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"⚠️ Erreur utilisateur_existe : {e}")
        return False


def get_user_info(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM utilisateurs WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"⚠️ Erreur get_user_info : {e}")
        return None


def get_user_status(user_id):
    info = get_user_info(user_id)
    if not info:
        return 'free', None
    return info['status'], info['date_expiration']


def enregistrer_utilisateur(user_id, username, first_name):
    try:
        if utilisateur_existe(user_id):
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO utilisateurs (user_id, username, first_name, status)
            VALUES (%s, %s, %s, 'free')
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username or "", first_name or ""))
        conn.commit()
        cur.close()
        conn.close()
        print(f"👤 Nouvel utilisateur : {first_name} ({user_id})")
        return True
    except Exception as e:
        print(f"⚠️ Erreur enregistrer_utilisateur : {e}")
        return False


def set_premium(user_id, date_expiration):
    try:
        if isinstance(date_expiration, str):
            date_expiration = datetime.strptime(date_expiration, "%Y-%m-%d %H:%M")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET status = 'premium', date_expiration = %s
            WHERE user_id = %s
        """, (date_expiration, user_id))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        if rows == 0:
            return False
        print(f"⭐ Utilisateur {user_id} passé en PREMIUM")
        return True
    except Exception as e:
        print(f"⚠️ Erreur set_premium : {e}")
        return False


def est_premium(user_id):
    status, expiration = get_user_status(user_id)
    if status != 'premium' or not expiration:
        return False
    try:
        return expiration > datetime.now()
    except Exception:
        return False


def get_statut_label(user_id):
    return "⭐ PREMIUM" if est_premium(user_id) else "🆓 FREE"


def incrementer_compteur(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compteurs_jour (user_id, date, compteur)
            VALUES (%s, %s, 1)
            ON CONFLICT (user_id, date)
            DO UPDATE SET compteur = compteurs_jour.compteur + 1
        """, (user_id, today))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erreur incrementer_compteur : {e}")


def get_compteur_jour(user_id):
    try:
        today = datetime.now().date()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT compteur FROM compteurs_jour WHERE user_id = %s AND date = %s",
            (user_id, today)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"⚠️ Erreur get_compteur_jour : {e}")
        return 0


def get_limite_jour(user_id):
    return LIMITE_PREMIUM_JOUR if est_premium(user_id) else LIMITE_FREE_JOUR


def peut_faire_pronostic(user_id):
    return get_compteur_jour(user_id) < get_limite_jour(user_id)
