import psycopg2
import psycopg2.extras
from datetime import datetime

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
)
from core.utils.logs import log_info, log_error

def get_connection():
    """Retourne une connexion à la base de données PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME, sslmode="require"
    )

def initialiser_tables():
    """Initialise toutes les tables de la base de données au démarrage."""
    with get_connection() as conn:
        with conn.cursor() as cur:
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

            # Paiements en attente
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

            # Codes Premium
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

            # Résultats des pronostics
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resultats_pronostics (
                    id SERIAL PRIMARY KEY,
                    date_match DATE,
                    home_team TEXT,
                    away_team TEXT,
                    pronostic_reco TEXT,
                    score_reel TEXT,
                    est_gagnant BOOLEAN,
                    date_creation TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_resultats_date ON resultats_pronostics(date_match)")

        conn.commit()
        log_info("Tables PostgreSQL prêtes (avec paiements + codes + resultats).", "DATABASE")

def get_taille_base():
    """Retourne la taille de la base en MB."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            taille = cur.fetchone()[0]
            return taille

def get_detail_tables():
    """Retourne la taille de chaque table."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    relname AS table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) AS size,
                    0 AS rows
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def nettoyer_logs_anciens(jours=30):
    """Supprime les logs admin de plus de X jours."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM logs_admin
                WHERE date_action < NOW() - INTERVAL '%s days'
            """, (jours,))
            rows = cur.rowcount
        conn.commit()
        log_info(f"{rows} ancien(s) log(s) supprimé(s)", "DATABASE")
        return rows

def nettoyer_paiements_anciens(jours=90):
    """Supprime les paiements traités de plus de X jours."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM paiements_attente
                WHERE statut != 'en_attente'
                AND date_validation < NOW() - INTERVAL '%s days'
            """, (jours,))
            rows = cur.rowcount
        conn.commit()
        log_info(f"{rows} ancien(s) paiement(s) supprimé(s)", "DATABASE")
        return rows
