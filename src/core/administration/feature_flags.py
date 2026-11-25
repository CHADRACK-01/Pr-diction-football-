# core/administration/feature_flags.py
"""
Gestion des interrupteurs de fonctionnalités (feature flags).

Permet d'activer/désactiver une fonctionnalité à chaud via la table
``fonctionnalites_actives`` de la base Turso, avec journalisation de chaque
bascule dans ``historique_features``.

Toutes les fonctions sont idempotentes et ne lèvent jamais d'exception
métier non attrapée : une erreur de base est journalisée et la fonction
retourne une valeur par défaut sûre.
"""

from __future__ import annotations

from typing import Any

from core.utils.logs import log_error
from users.database import db_execute, db_fetchone, db_fetchall


def est_active(feature_id: str | int) -> bool:
    """Vérifie si une fonctionnalité est active (par défaut : False).

    Args:
        feature_id: Identifiant de la fonctionnalité (str ou int).

    Returns:
        True si la fonctionnalité est active, False sinon ou en cas d'erreur.
    """
    try:
        row = db_fetchone(
            "SELECT actif FROM fonctionnalites_actives WHERE feature_id = ?",
            params=[str(feature_id)],
        )
    except Exception as e:
        log_error(
            message=f"Impossible de vérifier le feature flag '{feature_id}'",
            module="FEATURE_FLAGS",
            exception=e,
        )
        return False
    return bool(row[0]) if row else False


def _enregistrer_feature(
    feature_id: str | int,
    actif: bool,
    libelle: str | None = None,
    categorie: str | None = None,
    proprietaire: str | None = None,
) -> None:
    """Insère ou met à jour une fonctionnalité sans écraser ses métadonnées existantes.

    Les métadonnées (libelle, categorie, proprietaire) ne sont écrites que si
    la ligne n'existe pas encore ou si la valeur passée n'est pas None.
    """
    db_execute(
        "INSERT INTO fonctionnalites_actives "
        "(feature_id, actif, libelle, categorie, proprietaire, date_creation) "
        "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(feature_id) DO UPDATE SET "
        "actif = excluded.actif, "
        "libelle = COALESCE(excluded.libelle, fonctionnalites_actives.libelle), "
        "categorie = COALESCE(excluded.categorie, fonctionnalites_actives.categorie), "
        "proprietaire = COALESCE(excluded.proprietaire, fonctionnalites_actives.proprietaire)",
        params=[str(feature_id), 1 if actif else 0, libelle, categorie, proprietaire],
    )


def journaliser_bascule(feature_id: str | int, actif: bool, auteur_id: int | None = None) -> None:
    """Historise une bascule (non bloquant : la bascule reste effective en cas d'échec).

    Args:
        feature_id: Identifiant de la fonctionnalité.
        actif: Nouvel état (True = activé).
        auteur_id: ID de l'utilisateur ayant déclenché la bascule, si connu.
    """
    try:
        db_execute(
            "INSERT INTO historique_features (feature_id, actif, auteur_id, date_bascule) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            params=[str(feature_id), 1 if actif else 0, auteur_id],
        )
    except Exception as e:
        log_error(
            message=f"Impossible d'historiser la bascule de la fonctionnalité '{feature_id}'",
            module="FEATURE_FLAGS",
            exception=e,
        )


def activer_feature(
    feature_id: str | int,
    libelle: str | None = None,
    categorie: str | None = None,
    proprietaire: str | None = None,
    auteur_id: int | None = None,
) -> None:
    """Active une fonctionnalité (métadonnées optionnelles)."""
    _enregistrer_feature(
        feature_id, True, libelle=libelle, categorie=categorie, proprietaire=proprietaire
    )
    journaliser_bascule(feature_id, True, auteur_id)


def desactiver_feature(
    feature_id: str | int,
    libelle: str | None = None,
    categorie: str | None = None,
    proprietaire: str | None = None,
    auteur_id: int | None = None,
) -> None:
    """Désactive une fonctionnalité (métadonnées optionnelles)."""
    _enregistrer_feature(
        feature_id, False, libelle=libelle, categorie=categorie, proprietaire=proprietaire
    )
    journaliser_bascule(feature_id, False, auteur_id)


def lister_features() -> dict[str, bool]:
    """Retourne la liste de toutes les fonctionnalités et leur état.

    Returns:
        Dictionnaire {feature_id: actif_bool}. Vide en cas d'erreur.
    """
    try:
        rows = db_fetchall("SELECT feature_id, actif FROM fonctionnalites_actives")
    except Exception as e:
        log_error(
            message="Impossible de lister les feature flags",
            module="FEATURE_FLAGS",
            exception=e,
        )
        return {}
    return {row[0]: bool(row[1]) for row in rows}


def lister_catalogue() -> dict[str, dict[str, Any]]:
    """Retourne le catalogue des fonctionnalités avec leurs métadonnées.

    Returns:
        Dictionnaire {feature_id: {feature_id, actif, libelle, categorie,
        priorite, proprietaire, date_creation, date_expiration}}.
        Vide en cas d'erreur.
    """
    try:
        rows = db_fetchall(
            "SELECT feature_id, actif, libelle, categorie, priorite, proprietaire, "
            "date_creation, date_expiration FROM fonctionnalites_actives"
        )
    except Exception as e:
        log_error(
            message="Impossible de lister le catalogue des fonctionnalités",
            module="FEATURE_FLAGS",
            exception=e,
        )
        return {}

    catalogue: dict[str, dict[str, Any]] = {}
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
