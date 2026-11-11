# users/db.py
"""
Gestion de la base de données Turso (libsql).

Principes :
- Une seule fonction `get_connection()` centralisée
- Contexte manager `db_connection()` pour try/finally automatique
- Helpers `db_execute`, `db_fetchone`, `db_fetchall` avec logs enrichis
- Migration de colonnes robuste (PRAGMA + fallback)
- Aucune f-string SQL (paramètres liés uniquement)
"""

import os
import time
import libsql
from contextlib import contextmanager
from datetime import datetime

from core.utils.logs import log_info, log_error, log_warning

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")


# =========================================================
# CONNEXION CENTRALISÉE
# =========================================================
def get_connection():
    """
    Retourne une connexion Turso.
    Lève RuntimeError si la config est absente (ne devrait jamais arriver
    après verifier_configuration()).
    """
    if not TURSO_URL or not TURSO_TOKEN:
        raise RuntimeError(
            "TURSO_URL ou TURSO_TOKEN manquant. "
            "Impossible d'établir la connexion à la base."
        )
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


@contextmanager
def db_connection(db_context=None):
    """
    Context manager qui garantit la fermeture de la connexion,
    même en cas d'exception.

    Usage :
        with db_connection({"table": "utilisateurs"}) as conn:
            conn.execute(...)
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        log_error(
            message="Erreur DB dans un bloc contextuel",
            module="DATABASE",
            db_context=db_context,
            exception=e,
        )
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion DB",
                    module="DATABASE",
                    db_context=db_context,
                    exception=e,
                )


# =========================================================
# HELPERS DE HAUT NIVEAU (try/except + logs enrichis)
# =========================================================
def db_execute(query, params=None, db_context=None, commit=True):
    """
    Exécute une requête d'écriture avec logs détaillés en cas d'erreur.
    Retourne le rowcount (nombre de lignes affectées) ou None si échec.
    """
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)

    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(query, params or [])
        if commit:
            conn.commit()
        return cur.rowcount if hasattr(cur, "rowcount") else 0
    except Exception as e:
        log_error(
            message="Échec d'exécution SQL",
            module="DATABASE",
            db_context=ctx,
            exception=e,
        )
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion DB",
                    module="DATABASE",
                    db_context=ctx,
                    exception=e,
                )


def db_fetchone(query, params=None, db_context=None):
    """Exécute un SELECT et retourne la première ligne (ou None)."""
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)

    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(query, params or [])
        return cur.fetchone()
    except Exception as e:
        log_error(
            message="Échec de lecture SQL (fetchone)",
            module="DATABASE",
            db_context=ctx,
            exception=e,
        )
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion DB",
                    module="DATABASE",
                    db_context=ctx,
                    exception=e,
                )


def db_fetchall(query, params=None, db_context=None):
    """Exécute un SELECT et retourne toutes les lignes (liste vide si échec)."""
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)

    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(query, params or [])
        return cur.fetchall()
    except Exception as e:
        log_error(
            message="Échec de lecture SQL (fetchall)",
            module="DATABASE",
            db_context=ctx,
            exception=e,
        )
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion DB",
                    module="DATABASE",
                    db_context=ctx,
                    exception=e,
                )


def db_fetchone_dict(query, params=None, db_context=None):
    """Comme db_fetchone, mais retourne un dict (colonnes -> valeurs)."""
    conn = None
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)
    try:
        conn = get_connection()
        cur = conn.execute(query, params or [])
        row = cur.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    except Exception as e:
        log_error(
            message="Échec de lecture SQL (fetchone_dict)",
            module="DATABASE",
            db_context=ctx,
            exception=e,
        )
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion DB",
                    module="DATABASE",
                    db_context=ctx,
                    exception=e,
                )


# =========================================================
# INITIALISATION DES TABLES
# =========================================================
def _creer_table(conn, nom, sql):
    """Crée une table (idempotent)."""
    try:
        conn.execute(sql)
        conn.commit()
        log_info(f"Table '{nom}' vérifiée.", "DATABASE")
        return True
    except Exception as e:
        log_error(
            message=f"Impossible de créer la table '{nom}'",
            module="DATABASE",
            db_context={"table": nom, "query": sql[:200]},
            exception=e,
        )
        return False


def _ajouter_colonnes_manquantes(conn, table, colonnes):
    """
    Vérifie les colonnes existantes via PRAGMA table_info
    et ajoute celles qui manquent via ALTER TABLE.
    Gère le cas où PRAGMA n'est pas supporté (fallback : on tente l'ALTER
    directement et on ignore l'erreur "duplicate column").
    """
    existantes = set()

    # Tentative via PRAGMA
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        rows = cur.fetchall()
        existantes = {row[1] for row in rows}
        log_info(
            f"PRAGMA OK pour '{table}' : {len(existantes)} colonnes détectées.",
            "DATABASE",
        )
    except Exception as e:
        log_warning(
            message=f"PRAGMA non supporté pour '{table}', on tente ALTER en aveugle",
            module="DATABASE",
            db_context={"table": table},
            exception=e,
        )

    for nom_col, type_col in colonnes.items():
        if nom_col in existantes:
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {nom_col} {type_col}")
            conn.commit()
            log_info(
                f"Colonne '{nom_col}' ajoutée à la table '{table}'.",
                "DATABASE",
            )
        except Exception as e:
            msg = str(e).lower()
            # Si la colonne existe déjà (PRAGMA indisponible), c'est OK
            if "duplicate column" in msg or "already exists" in msg:
                log_info(
                    f"Colonne '{nom_col}' déjà présente dans '{table}'.",
                    "DATABASE",
                )
            else:
                log_error(
                    message=f"Impossible d'ajouter la colonne '{nom_col}' à '{table}'",
                    module="DATABASE",
                    db_context={"table": table, "column": nom_col, "type": type_col},
                    exception=e,
                )


def initialiser_tables():
    """Initialise toutes les tables de la base (idempotent, sans destruction)."""
    log_info("Début de l'initialisation des tables...", "DATABASE")

    conn = None
    try:
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
                    competition TEXT,
                    pronostic_reco TEXT,
                    score_predit TEXT,
                    score_reel TEXT,
                    est_gagnant INTEGER,
                    tentatives_verification INTEGER DEFAULT 0,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "sessions_pronostic": """
                CREATE TABLE IF NOT EXISTS sessions_pronostic (
                    user_id INTEGER PRIMARY KEY,
                    competition TEXT,
                    etape TEXT,
                    equipe_dom TEXT,
                    equipe_ext TEXT,
                    equipes_dispo TEXT,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_maj TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
        }

        for nom, sql in tables.items():
            _creer_table(conn, nom, sql)

        # Migration : colonnes manquantes dans matchs
        colonnes_matchs = {
            "hs": "INTEGER", "as_shots": "INTEGER",
            "hst": "INTEGER", "ast": "INTEGER",
            "hc": "INTEGER", "ac": "INTEGER",
            "hf": "INTEGER", "af": "INTEGER",
            "hy": "INTEGER", "ay": "INTEGER",
            "hr": "INTEGER", "ar": "INTEGER",
            "b365h": "REAL", "b365d": "REAL", "b365a": "REAL",
        }
        _ajouter_colonnes_manquantes(conn, "matchs", colonnes_matchs)

        # Migration : colonnes manquantes dans resultats_pronostics
        colonnes_resultats = {
            "competition": "TEXT",
            "score_predit": "TEXT",
            "tentatives_verification": "INTEGER DEFAULT 0",
        }
        _ajouter_colonnes_manquantes(conn, "resultats_pronostics", colonnes_resultats)

        # Migration : colonnes manquantes dans sessions_pronostic
        colonnes_sessions = {
            "etape": "TEXT",
            "equipe_dom": "TEXT",
            "equipe_ext": "TEXT",
            "equipes_dispo": "TEXT",
            "date_creation": "TEXT",
            "date_maj": "TEXT",
        }
        _ajouter_colonnes_manquantes(conn, "sessions_pronostic", colonnes_sessions)

        # Vérification finale
        try:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            noms = [r[0] for r in result]
            log_info(f"Tables existantes ({len(noms)}) : {noms}", "DATABASE")
        except Exception as e:
            log_warning(
                message="Impossible de lister les tables",
                module="DATABASE",
                exception=e,
            )
    except Exception as e:
        log_error(
            message="Erreur critique lors de l'initialisation des tables",
            module="DATABASE",
            exception=e,
        )
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion après init",
                    module="DATABASE",
                    exception=e,
                )

    log_info("Initialisation terminée.", "DATABASE")


# =========================================================
# UTILITAIRES ADMIN
# =========================================================
def get_taille_base():
    """Retourne la taille de la base en MB (ou 'Erreur' si échec)."""
    try:
        row = db_fetchone("""
            SELECT page_count * page_size as size
            FROM pragma_page_count(), pragma_page_size()
        """, db_context={"table": "pragma"})
        if row and row[0]:
            return f"{row[0] / 1024 / 1024:.2f} MB"
        return "Inconnue"
    except Exception as e:
        log_error(
            message="Impossible de calculer la taille de la base",
            module="DATABASE",
            exception=e,
        )
        return "Erreur"


def get_detail_tables():
    """Retourne le nombre de lignes par table."""
    tables = [
        "utilisateurs", "matchs", "models_cache",
        "paiements_attente", "codes_premium", "logs_admin",
        "resultats_pronostics", "sessions_pronostic",
    ]
    resultats = []
    for table in tables:
        try:
            # ⚠️ Pas de f-string SQL : on whitelist les tables
            if table not in tables:
                continue
            row = db_fetchone(
                f"SELECT COUNT(*) FROM {table}",
                db_context={"table": table},
            )
            count = row[0] if row else 0
            resultats.append({"table_name": table, "size": f"{count} lignes"})
        except Exception as e:
            log_warning(
                message=f"Impossible de lire la table '{table}'",
                module="DATABASE",
                db_context={"table": table},
                exception=e,
            )
            resultats.append({"table_name": table, "size": "❌ erreur"})
    return resultats


def nettoyer_logs_anciens(jours: int = 30) -> int:
    """Supprime les logs admin de plus de X jours. Retourne le nombre supprimé."""
    if not isinstance(jours, int) or jours <= 0 or jours > 3650:
        log_warning(
            message=f"Paramètre 'jours' invalide : {jours}",
            module="DATABASE",
            extra={"jours": jours},
        )
        return 0
    query = "DELETE FROM logs_admin WHERE date_action < datetime('now', ?)"
    rowcount = db_execute(
        query,
        params=[f"-{jours} days"],
        db_context={"table": "logs_admin", "operation": "cleanup"},
    )
    if rowcount is None:
        return 0
    log_info(f"{rowcount} logs de plus de {jours}j supprimés.", "DATABASE")
    return rowcount


def nettoyer_paiements_anciens(jours: int = 90) -> int:
    """Supprime les paiements traités de plus de X jours."""
    if not isinstance(jours, int) or jours <= 0 or jours > 3650:
        log_warning(
            message=f"Paramètre 'jours' invalide : {jours}",
            module="DATABASE",
            extra={"jours": jours},
        )
        return 0
    query = """
        DELETE FROM paiements_attente
        WHERE statut != 'en_attente'
        AND date_validation < datetime('now', ?)
    """
    rowcount = db_execute(
        query,
        params=[f"-{jours} days"],
        db_context={"table": "paiements_attente", "operation": "cleanup"},
    )
    if rowcount is None:
        return 0
    log_info(f"{rowcount} paiements de plus de {jours}j supprimés.", "DATABASE")
    return rowcount
