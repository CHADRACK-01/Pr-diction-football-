# core/feature_flags.py
from users.db import db_execute, db_fetchone, db_fetchall

from core.utils.logs import log_error

def est_active(feature_id):
    """Vérifie si une fonctionnalité est active (par défaut : False)."""
    row = db_fetchone(
        "SELECT actif FROM fonctionnalites_actives WHERE feature_id = ?",
        params=[str(feature_id)]
    )
    return bool(row[0]) if row else False

def _enregistrer_feature(feature_id, actif, libelle=None, categorie=None, proprietaire=None):
    """Insère ou met à jour une fonctionnalité sans écraser ses métadonnées existantes."""
    db_execute(
        "INSERT INTO fonctionnalites_actives "
        "(feature_id, actif, libelle, categorie, proprietaire, date_creation) "
        "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(feature_id) DO UPDATE SET "
        "actif = excluded.actif, "
        "libelle = COALESCE(excluded.libelle, fonctionnalites_actives.libelle), "
        "categorie = COALESCE(excluded.categorie, fonctionnalites_actives.categorie), "
        "proprietaire = COALESCE(excluded.proprietaire, fonctionnalites_actives.proprietaire)",
        params=[str(feature_id), 1 if actif else 0, libelle, categorie, proprietaire]
    )

def journaliser_bascule(feature_id, actif, auteur_id=None):
    """Historise une bascule (non bloquant : la bascule reste effective en cas d'échec)."""
    try:
        db_execute(
            "INSERT INTO historique_features (feature_id, actif, auteur_id, date_bascule) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            params=[str(feature_id), 1 if actif else 0, auteur_id]
        )
    except Exception as e:
        log_error(
            message=f"Impossible d'historiser la bascule de la fonctionnalité '{feature_id}'",
            module="FEATURE_FLAGS",
            exception=e,
        )

def activer_feature(feature_id, libelle=None, categorie=None, proprietaire=None, auteur_id=None):
    """Active une fonctionnalité (métadonnées optionnelles)."""
    _enregistrer_feature(
        feature_id, True, libelle=libelle, categorie=categorie, proprietaire=proprietaire
    )
    journaliser_bascule(feature_id, True, auteur_id)

def desactiver_feature(feature_id, libelle=None, categorie=None, proprietaire=None, auteur_id=None):
    """Désactive une fonctionnalité (métadonnées optionnelles)."""
    _enregistrer_feature(
        feature_id, False, libelle=libelle, categorie=categorie, proprietaire=proprietaire
    )
    journaliser_bascule(feature_id, False, auteur_id)

def lister_features():
    """Retourne la liste de toutes les fonctionnalités et leur état ({feature_id: bool})."""
    rows = db_fetchall("SELECT feature_id, actif FROM fonctionnalites_actives")
    return {row[0]: bool(row[1]) for row in rows}

def lister_catalogue():
    """Retourne le catalogue des fonctionnalités avec leurs métadonnées."""
    rows = db_fetchall(
        "SELECT feature_id, actif, libelle, categorie, priorite, proprietaire, "
        "date_creation, date_expiration FROM fonctionnalites_actives"
    )
    catalogue = {}
    for row in rows:
        feature_id = row[0]
        catalogue[feature_id] = {
            "feature_id": feature_id,
            "actif": bool(row[1]),
            "libelle": row[2] or str(feature_id),
            "categorie": row[3],
            "priorite": row[4],
            "proprietaire": row[5],
            "date_creation": row[6],
            "date_expiration": row[7],
        }
    return catalogue