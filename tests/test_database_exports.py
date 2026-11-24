"""Contrats d'import pour la couche base de données structurée."""


def test_exports_database_sont_disponibles():
    from users.database import DatabaseError, db_connection, get_connection

    assert issubclass(DatabaseError, Exception)
    assert callable(db_connection)
    assert callable(get_connection)


def test_exports_maintenance_sont_disponibles():
    from users.database.maintenance import (
        get_detail_tables,
        get_taille_base,
        nettoyer_logs_anciens,
        nettoyer_paiements_anciens,
    )

    assert callable(get_detail_tables)
    assert callable(get_taille_base)
    assert callable(nettoyer_logs_anciens)
    assert callable(nettoyer_paiements_anciens)
