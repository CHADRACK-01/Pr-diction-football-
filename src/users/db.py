# users/db.py
"""
Shim de compatibilité historique.

Tous les helpers de base de données vivent désormais dans
``users.database.queries`` et ``users.database.connection``.
Ce module ré-exporte les symboles historiques pour ne pas casser les
imports existants (``from users.db import ...``).
"""

from users.database.connection import (  # noqa: F401
    get_connection,
    db_connection,
)
from users.database.queries import (  # noqa: F401
    db_execute,
    db_fetchone,
    db_fetchall,
    db_fetchone_dict,
    db_fetchone_strict,
)
from users.database.maintenance import (  # noqa: F401
    initialiser_tables,
)

__all__ = [
    "get_connection",
    "db_connection",
    "db_execute",
    "db_fetchone",
    "db_fetchall",
    "db_fetchone_dict",
    "db_fetchone_strict",
    "initialiser_tables",
]
