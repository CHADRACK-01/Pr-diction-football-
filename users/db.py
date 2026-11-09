import libsql
import os

from core.utils.logs import log_info

# ⚠️ Utilise des variables d'environnement pour la sécurité
TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")


def get_connection():
    """Retourne une connexion à la base de données Turso via libsql."""
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


def initialiser_tables():
    """Initialise toutes les tables de la base de données au démarrage."""
    conn = get_connection()
    
    # 1. Utilisateurs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            status TEXT DEFAULT 'free',
            date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
            date_expiration TEXT,
            notifications_actives INTEGER DEFAULT 1,
            langue TEXT DEFAULT 'fr',
            parrain_id INTEGER,
            methode_paiement TEXT
        )
    """)
    
    # 2. Compteurs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compteurs_jour (
            user_id INTEGER,
            date TEXT,
            compteur INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        )
    """)
    
    # 3. Matchs (gardée pour compatibilité avec ton ancien code)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS matchs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            home_team TEXT,
            away_team TEXT,
            fthg INTEGER, ftag INTEGER, ftr TEXT,
            hthg INTEGER, htag INTEGER, htr TEXT,
            hs INTEGER, as_shots INTEGER, hst INTEGER, ast INTEGER,
            hc INTEGER, ac INTEGER, hf INTEGER, af INTEGER,
            hy INTEGER, ay INTEGER, hr INTEGER, ar INTEGER,
            b365h REAL, b365d REAL, b365a REAL,
            competition TEXT,
            UNIQUE(date, home_team, away_team, competition)
        )
    """)
    
    # 4. NOUVELLE TABLE : Cache des modèles (format simplifié)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS models_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data BLOB,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Paramètres
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            cle TEXT PRIMARY KEY,
            valeur TEXT,
            description TEXT,
            modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. Admins
    conn.execute("""
        CREATE TABLE IF NOT EXISTS administrateurs (
            user_id INTEGER PRIMARY KEY,
            nom TEXT,
            ajoute_le TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 7. Bannis
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bannis (
            user_id INTEGER PRIMARY KEY,
            raison TEXT,
            banni_le TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 8. Logs admin
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            details TEXT,
            date_action TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 9. Paiements en attente
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paiements_attente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            abonnement TEXT,
            montant INTEGER,
            preuve_photo_id TEXT,
            statut TEXT DEFAULT 'en_attente',
            date_demande TEXT DEFAULT CURRENT_TIMESTAMP,
            date_validation TEXT,
            admin_id INTEGER
        )
    """)
    
    # 10. Codes Premium
    conn.execute("""
        CREATE TABLE IF NOT EXISTS codes_premium (
            code TEXT PRIMARY KEY,
            jours INTEGER,
            utilise INTEGER DEFAULT 0,
            utilise_par INTEGER,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
            date_utilisation TEXT
        )
    """)
    
    # 11. Résultats des pronostics
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resultats_pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_match TEXT,
            home_team TEXT,
            away_team TEXT,
            pronostic_reco TEXT,
            score_reel TEXT,
            est_gagnant INTEGER,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 12. Sessions de pronostic
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions_pronostic (
            user_id INTEGER PRIMARY KEY,
            competition TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    log_info("Tables Turso prêtes (12 tables + models_cache).", "DATABASE")


def get_taille_base():
    """Retourne la taille de la base en MB."""
    conn = get_connection()
    result = conn.execute("""
        SELECT page_count * page_size as size 
        FROM pragma_page_count(), pragma_page_size()
    """).fetchone()
    conn.close()
    if result and result[0]:
        return f"{result[0] / 1024 / 1024:.2f} MB"
    return "Inconnue"


def get_detail_tables():
    """Retourne la taille de chaque table."""
    conn = get_connection()
    tables = ["utilisateurs", "matchs", "models_cache", "paiements_attente", "codes_premium", "logs_admin"]
    resultats = []
    for table in tables:
        res = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        resultats.append({"table_name": table, "size": f"{res[0]} lignes"})
    conn.close()
    return resultats


def nettoyer_logs_anciens(jours=30):
    """Supprime les logs admin de plus de X jours."""
    conn = get_connection()
    conn.execute(f"""
        DELETE FROM logs_admin
        WHERE date_action < datetime('now', '-{jours} days')
    """)
    conn.commit()
    conn.close()
    log_info(f"Logs de plus de {jours} jours supprimés.", "DATABASE")
    return True


def nettoyer_paiements_anciens(jours=90):
    """Supprime les paiements traités de plus de X jours."""
    conn = get_connection()
    conn.execute(f"""
        DELETE FROM paiements_attente
        WHERE statut != 'en_attente'
        AND date_validation < datetime('now', '-{jours} days')
    """)
    conn.commit()
    conn.close()
    log_info(f"Paiements de plus de {jours} jours supprimés.", "DATABASE")
    return True
