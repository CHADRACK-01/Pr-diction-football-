"""Connexion centrale Turso/libSQL."""

import os
from contextlib import contextmanager

import libsql

from core.utils.logs import log_error, log_warning

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")


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
    except Exception as exc:
        log_error(
            message="Erreur DB dans un bloc contextuel",
            module="DATABASE",
            db_context=db_context,
            exception=exc,
        )
        raise
    finally:
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
