import psycopg2
import psycopg2.extras

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
)


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME, sslmode="require"
    )


def initialiser_tables():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Table utilisateurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                status TEXT DEFAULT 'free',
                date_inscription TIMESTAMP DEFAULT NOW(),
                date_expiration TIMESTAMP,
                notifications_actives BOOLEAN DEFAULT TRUE,
                langue TEXT DEFAULT 'fr'
            )
        """)

        # Table compteurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compteurs_jour (
                user_id BIGINT,
                date DATE,
                compteur INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)

        # Table matchs
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

        # Cache du modèle
        cur.execute("""
            CREATE TABLE IF NOT EXISTS model_cache (
                id INTEGER PRIMARY KEY DEFAULT 1,
                modele BYTEA,
                precision REAL,
                nb_matchs INTEGER,
                date_creation TIMESTAMP DEFAULT NOW(),
                CONSTRAINT single_row CHECK (id = 1)
            )
        """)

        # Paramètres dynamiques
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parametres (
                cle TEXT PRIMARY KEY,
                valeur TEXT,
                description TEXT,
                modifie_le TIMESTAMP DEFAULT NOW()
            )
        """)

        # Administrateurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS administrateurs (
                user_id BIGINT PRIMARY KEY,
                nom TEXT,
                ajoute_le TIMESTAMP DEFAULT NOW()
            )
        """)

        # Bannis
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bannis (
                user_id BIGINT PRIMARY KEY,
                raison TEXT,
                banni_le TIMESTAMP DEFAULT NOW()
            )
        """)

        # Logs admin
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs_admin (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT,
                action TEXT,
                details TEXT,
                date_action TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tables PostgreSQL prêtes (users, matchs, cache, admin, langue).")
    except Exception as e:
        print(f"❌ Erreur init tables : {e}")
