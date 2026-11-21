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





def initialiser_tables():
    from users import schema

    log_info("Début de l'initialisation des tables...", "DATABASE")

    conn = None
    try:
        conn = get_connection()

        schema.synchroniser_schema(conn, _ajouter_colonnes_manquantes)

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
