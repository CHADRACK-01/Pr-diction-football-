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

        # Utilisateurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                status TEXT DEFAULT 'free',
                date_inscription TIMESTAMP DEFAULT NOW(),
                date_expiration TIMESTAMP,
                notifications_actives BOOLEAN DEFAULT TRUE,
                langue TEXT DEFAULT 'fr',
                parrain_id BIGINT DEFAULT NULL,
                methode_paiement TEXT DEFAULT NULL
            )
        """)

        # Compteurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compteurs_jour (
                user_id BIGINT,
                date DATE,
                compteur INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)

        # Matchs
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

        # Cache modèle
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

        # Paramètres
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parametres (
                cle TEXT PRIMARY KEY,
                valeur TEXT,
                description TEXT,
                modifie_le TIMESTAMP DEFAULT NOW()
            )
        """)

        # Admins
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

        # ⚠️ NOUVEAU : Paiements en attente
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paiements_attente (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                abonnement TEXT,
                montant INTEGER,
                preuve_photo_id TEXT,
                statut TEXT DEFAULT 'en_attente',
                date_demande TIMESTAMP DEFAULT NOW(),
                date_validation TIMESTAMP,
                admin_id BIGINT
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_paiements_statut ON paiements_attente(statut)")

        # ⚠️ NOUVEAU : Codes Premium
        cur.execute("""
            CREATE TABLE IF NOT EXISTS codes_premium (
                code TEXT PRIMARY KEY,
                jours INTEGER,
                utilise BOOLEAN DEFAULT FALSE,
                utilise_par BIGINT,
                date_creation TIMESTAMP DEFAULT NOW(),
                date_utilisation TIMESTAMP
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_codes_utilise ON codes_premium(utilise)")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tables PostgreSQL prêtes (avec paiements + codes).")
    except Exception as e:
        print(f"❌ Erreur init tables : {e}")


def get_taille_base():
    """Retourne la taille de la base en MB."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        taille = cur.fetchone()[0]
        cur.close()
        conn.close()
        return taille
    except Exception as e:
        print(f"⚠️ Erreur get_taille_base : {e}")
        return "Inconnue"


def get_detail_tables():
    """Retourne la taille de chaque table."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT 
                relname AS table_name,
                pg_size_pretty(pg_total_relation_size(relid)) AS size,
                n_live_tup AS rows
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"⚠️ Erreur get_detail_tables : {e}")
        return []


def nettoyer_logs_anciens(jours=30):
    """Supprime les logs admin de plus de X jours."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM logs_admin
            WHERE date_action < NOW() - INTERVAL '%s days'
        """, (jours,))
        rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"🧹 {rows} ancien(s) log(s) supprimé(s)")
        return rows
    except Exception as e:
        print(f"⚠️ Erreur nettoyer_logs_anciens : {e}")
        return 0


def nettoyer_paiements_anciens(jours=90):
    """Supprime les paiements traités de plus de X jours."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM paiements_attente
            WHERE statut != 'en_attente'
            AND date_validation < NOW() - INTERVAL '%s days'
        """, (jours,))
        rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"🧹 {rows} ancien(s) paiement(s) supprimé(s)")
        return rows
    except Exception as e:
        print(f"⚠️ Erreur nettoyer_paiements_anciens : {e}")
        return 0
