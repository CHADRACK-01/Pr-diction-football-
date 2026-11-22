# users/db.py
"""
Gestion de la base de données Turso (libsql).
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
    if not TURSO_URL or not TURSO_TOKEN:
        raise RuntimeError(
            "TURSO_URL ou TURSO_TOKEN manquant. "
            "Impossible d'établir la connexion à la base."
        )
    return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)


@contextmanager
def db_connection(db_context=None):
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
# HELPERS DE HAUT NIVEAU
# =========================================================
def db_execute(query, params=None, db_context=None, commit=True):
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
    existantes = set()
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


def _assurer_schema_catalogue(conn):
    """Crée et migre les tables du catalogue des fonctionnalités.

    À appeler lors de l'initialisation de la base, à côté des appels existants
    à _ajouter_colonnes_manquantes (matchs, resultats_pronostics, sessions_pronostic).
    """
    colonnes_features = {
        "libelle": "TEXT",
        "categorie": "TEXT",
        "priorite": "INTEGER",
        "proprietaire": "TEXT",
        "date_creation": "TEXT",
        "date_expiration": "TEXT",
    }
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS fonctionnalites_actives ("
            "feature_id TEXT PRIMARY KEY, "
            "actif INTEGER NOT NULL DEFAULT 0, "
            "libelle TEXT, "
            "categorie TEXT, "
            "priorite INTEGER, "
            "proprietaire TEXT, "
            "date_creation TEXT, "
            "date_expiration TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS historique_features ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "feature_id TEXT NOT NULL, "
            "actif INTEGER NOT NULL, "
            "auteur_id INTEGER, "
            "date_bascule TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
    except Exception as e:
        log_error(
            message="Impossible de créer les tables du catalogue des fonctionnalités",
            module="DATABASE",
            exception=e,
        )
    _ajouter_colonnes_manquantes(conn, "fonctionnalites_actives", colonnes_features)


def initialiser_tables():
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
            # NOUVELLE TABLE : Gestion des fonctionnalités (Feature Flags)
            "fonctionnalites_actives": """
                CREATE TABLE IF NOT EXISTS fonctionnalites_actives (
                    feature_id TEXT PRIMARY KEY,
                    actif INTEGER DEFAULT 0
                )
            """,
            # NOUVELLE TABLE : Bankroll (core/bankroll.py)
            "bankroll": """
                CREATE TABLE IF NOT EXISTS bankroll (
                    user_id INTEGER PRIMARY KEY,
                    montant_total REAL DEFAULT 0,
                    strategie TEXT DEFAULT 'kelly_fractionne',
                    pourcentage_mise REAL DEFAULT 2.0
                )
            """,
            # NOUVELLE TABLE : Équipes favorites (core/equipes_favorites.py)
            "equipes_favorites": """
                CREATE TABLE IF NOT EXISTS equipes_favorites (
                    user_id INTEGER,
                    equipe TEXT,
                    date_ajout TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, equipe)
                )
            """,
            # NOUVELLE TABLE : Codes promo (core/codes_promo.py)
            "codes_promo": """
                CREATE TABLE IF NOT EXISTS codes_promo (
                    code TEXT PRIMARY KEY,
                    type_reduction TEXT,
                    valeur REAL,
                    limite_utilisation INTEGER DEFAULT 0,
                    deja_utilise INTEGER DEFAULT 0,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
        }

        for nom, sql in tables.items():
            _creer_table(conn, nom, sql)

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

        colonnes_resultats = {
            "competition": "TEXT",
            "score_predit": "TEXT",
            "tentatives_verification": "INTEGER DEFAULT 0",
        }
        _ajouter_colonnes_manquantes(conn, "resultats_pronostics", colonnes_resultats)

        colonnes_sessions = {
            "etape": "TEXT",
            "equipe_dom": "TEXT",
            "equipe_ext": "TEXT",
            "equipes_dispo": "TEXT",
            "date_creation": "TEXT",
            "date_maj": "TEXT",
        }
        _ajouter_colonnes_manquantes(conn, "sessions_pronostic", colonnes_sessions)

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
    tables = [
        "utilisateurs", "matchs", "models_cache",
        "paiements_attente", "codes_premium", "logs_admin",
        "resultats_pronostics", "sessions_pronostic",
        "fonctionnalites_actives",
        "bankroll", "equipes_favorites", "codes_promo",
    ]
    resultats = []
    for table in tables:
        try:
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


# =========================================================
# VERSIONS STRICTES (ajoutées pour les chemins critiques)
# Contrairement aux helpers ci-dessus, ces fonctions ne renvoient JAMAIS une
# valeur vide en cas d'erreur : elles lèvent DatabaseError. Ainsi, une panne
# ne peut pas être prise pour « aucune donnée » (ex. compteur à 0).
# =========================================================
class DatabaseError(Exception):
    """Erreur de base de données remontée explicitement."""


def db_fetchone_strict(query, params=None, db_context=None):
    """Comme db_fetchone, mais lève DatabaseError en cas d'erreur."""
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
            message="Échec de lecture SQL (fetchone_strict)",
            module="DATABASE",
            db_context=ctx,
            exception=e,
        )
        raise DatabaseError(str(e)) from e
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
