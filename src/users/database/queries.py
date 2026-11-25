"""Helpers SQL standardisés et requêtes strictes."""

from core.utils.logs import log_error, log_warning
from users.database.connection import get_connection
from users.database.exceptions import DatabaseError


def _fermer(conn, db_context):
    if conn is not None:
        try:
            conn.close()
        except Exception as exc:
            log_warning(
                message="Impossible de fermer la connexion DB",
                module="DATABASE",
                db_context=db_context,
                exception=exc,
            )


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
    except Exception as exc:
        log_error(message="Échec d'exécution SQL", module="DATABASE", db_context=ctx, exception=exc)
        return None
    finally:
        _fermer(conn, ctx)


def db_fetchone(query, params=None, db_context=None):
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)
    conn = None
    try:
        conn = get_connection()
        return conn.execute(query, params or []).fetchone()
    except Exception as exc:
        log_error(message="Échec de lecture SQL (fetchone)", module="DATABASE", db_context=ctx, exception=exc)
        return None
    finally:
        _fermer(conn, ctx)


def db_fetchall(query, params=None, db_context=None):
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)
    conn = None
    try:
        conn = get_connection()
        return conn.execute(query, params or []).fetchall()
    except Exception as exc:
        log_error(message="Échec de lecture SQL (fetchall)", module="DATABASE", db_context=ctx, exception=exc)
        return []
    finally:
        _fermer(conn, ctx)


def db_fetchone_dict(query, params=None, db_context=None):
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)
    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(query, params or [])
        row = cur.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    except Exception as exc:
        log_error(message="Échec de lecture SQL (fetchone_dict)", module="DATABASE", db_context=ctx, exception=exc)
        return None
    finally:
        _fermer(conn, ctx)


def db_fetchone_strict(query, params=None, db_context=None):
    ctx = dict(db_context or {})
    ctx.setdefault("query", query)
    ctx.setdefault("params", params)
    conn = None
    try:
        conn = get_connection()
        return conn.execute(query, params or []).fetchone()
    except Exception as exc:
        log_error(message="Échec de lecture SQL (fetchone_strict)", module="DATABASE", db_context=ctx, exception=exc)
        raise DatabaseError(str(exc)) from exc
    finally:
        _fermer(conn, ctx)
