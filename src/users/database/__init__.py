"""API structurée de la couche de persistance."""

from users.database.connection import db_connection, get_connection
from users.database.exceptions import DatabaseError
from users.database.maintenance import (
    get_detail_tables,
    get_taille_base,
    nettoyer_logs_anciens,
    nettoyer_paiements_anciens,
)
from users.database.queries import (
    db_execute,
    db_fetchall,
    db_fetchone,
    db_fetchone_dict,
    db_fetchone_strict,
)

__all__ = [
    "DatabaseError",
    "db_connection",
    "db_execute",
    "db_fetchall",
    "db_fetchone",
    "db_fetchone_dict",
    "db_fetchone_strict",
    "get_connection",
    "get_detail_tables",
    "get_taille_base",
    "nettoyer_logs_anciens",
    "nettoyer_paiements_anciens",
]
