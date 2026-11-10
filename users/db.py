import libsql
import os

from core.utils.logs import log_info, log_error, log_warning

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")


def get_connection():
    """Retourne une connexion à la base de données Turso via libsql."""
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


def _executer_et_commit(conn, sql, nom_table):
    """Exécute une requête SQL et force le commit (avec log d'erreur explicite)."""
    try:
        conn.execute(sql)
        conn.commit()
        log_info(f"Table '{nom_table}' créée ou vérifiée.", "DATABASE")
    except Exception as e:
        log_error(
            message=f"Impossible de créer la table '{nom_table}'",
            module="DATABASE",
            exception=e
        )


def initialiser_tables():
    """Initialise toutes les tables de la base de données au démarrage."""
    log_info("Début de la création des tables...", "DATABASE")
    conn = get_connection()
    
    tables = {
        "utilisateurs": """
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
        """,
        "compteurs_jour": """
            CREATE TABLE IF NOT EXISTS compteurs_jour (
                user_id INTEGER,
                date TEXT,
                compteur INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """,
        "matchs": """
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
        """,
        "models_cache": """
            CREATE TABLE IF NOT EXISTS models_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data BLOB,
                date_creation TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "parametres": """
            CREATE TABLE IF NOT EXISTS parametres (
                cle TEXT PRIMARY KEY,
                valeur TEXT,
                description TEXT,
                modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "administrateurs": """
            CREATE TABLE IF NOT EXISTS administrateurs (
                user_id INTEGER PRIMARY KEY,
                nom TEXT,
                ajoute_le TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "bannis": """
            CREATE TABLE IF NOT EXISTS bannis (
                user_id INTEGER PRIMARY KEY,
                raison TEXT,
                banni_le TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "logs_admin": """
            CREATE TABLE IF NOT EXISTS logs_admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                details TEXT,
                date_action TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "paiements_attente": """
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
        """,
        "codes_premium": """
            CREATE TABLE IF NOT EXISTS codes_premium (
                code TEXT PRIMARY KEY,
                jours INTEGER,
                utilise INTEGER DEFAULT 0,
                utilise_par INTEGER,
                date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                date_utilisation TEXT
            )
        """,
        "resultats_pronostics": """
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
        """,
        "sessions_pronostic": """
            CREATE TABLE IF NOT EXISTS sessions_pronostic (
                user_id INTEGER PRIMARY KEY,
                competition TEXT
            )
        """,
    }
    
    for nom, sql in tables.items():
        _executer_et_commit(conn, sql, nom)
    
    # Vérification finale : est-ce que les tables existent vraiment ?
    try:
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        noms_tables = [r[0] for r in result]
        log_info(f"Tables existantes : {noms_tables}", "DATABASE")
    except Exception as e:
        log_error("Impossible de vérifier les tables existantes", "DATABASE", exception=e)
    finally:
        conn.close()
    
    log_info("Initialisation de la base de données terminée.", "DATABASE")


def get_taille_base():
    """Retourne la taille de la base en MB."""
    conn = get_connection()
    try:
        result = conn.execute("""
            SELECT page_count * page_size as size 
            FROM pragma_page_count(), pragma_page_size()
        """).fetchone()
        if result and result[0]:
            return f"{result[0] / 1024 / 1024:.2f} MB"
        return "Inconnue"
    except Exception as e:
        log_error("Impossible de calculer la taille de la base", "DATABASE", exception=e)
        return "Erreur"
    finally:
        conn.close()


def get_detail_tables():
    """Retourne la taille de chaque table."""
    conn = get_connection()
    tables = ["utilisateurs", "matchs", "models_cache", "paiements_attente", "codes_premium", "logs_admin"]
    resultats = []
    
    for table in tables:
        try:
            res = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            resultats.append({"table_name": table, "size": f"{res[0]} lignes"})
        except Exception as e:
            log_warning(f"Impossible de lire la table '{table}'", "DATABASE")
            resultats.append({"table_name": table, "size": "❌ n'existe pas"})
    
    conn.close()
    return resultats


def nettoyer_logs_anciens(jours=30):
    """Supprime les logs admin de plus de X jours."""
    conn = get_connection()
    try:
        conn.execute(f"DELETE FROM logs_admin WHERE date_action < datetime('now', '-{jours} days')")
        conn.commit()
        log_info(f"Logs de plus de {jours} jours supprimés.", "DATABASE")
        return True
    except Exception as e:
        log_error(f"Impossible de supprimer les logs de plus de {jours} jours", "DATABASE", exception=e)
        return False
    finally:
        conn.close()


def nettoyer_paiements_anciens(jours=90):
    """Supprime les paiements traités de plus de X jours."""
    conn = get_connection()
    try:
        conn.execute(f"""
            DELETE FROM paiements_attente
            WHERE statut != 'en_attente'
            AND date_validation < datetime('now', '-{jours} days')
        """)
        conn.commit()
        log_info(f"Paiements de plus de {jours} jours supprimés.", "DATABASE")
        return True
    except Exception as e:
        log_error(f"Impossible de supprimer les paiements de plus de {jours} jours", "DATABASE", exception=e)
        return False
    finally:
        conn.close()
