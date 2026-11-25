"""Inspection et nettoyage de la base de données."""

from core.utils.logs import log_error, log_info, log_warning
from users.database.queries import db_execute, db_fetchone


def get_taille_base():
    try:
        row = db_fetchone(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()",
            db_context={"table": "pragma"},
        )
        if row and row[0]:
            return f"{row[0] / 1024 / 1024:.2f} MB"
        return "Inconnue"
    except Exception as exc:
        log_error(
            message="Impossible de calculer la taille de la base",
            module="DATABASE",
            exception=exc,
        )
        return "Erreur"


def get_detail_tables():
    tables = [
        "utilisateurs", "matchs", "models_cache", "paiements_attente",
        "codes_premium", "logs_admin", "resultats_pronostics",
        "sessions_pronostic", "fonctionnalites_actives", "bankroll",
        "equipes_favorites", "codes_promo",
    ]
    resultats = []
    for table in tables:
        try:
            row = db_fetchone(
                f"SELECT COUNT(*) FROM {table}",
                db_context={"table": table},
            )
            count = row[0] if row else 0
            resultats.append({"table_name": table, "size": f"{count} lignes"})
        except Exception as exc:
            log_warning(
                message=f"Impossible de lire la table '{table}'",
                module="DATABASE",
                db_context={"table": table},
                exception=exc,
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

    rowcount = db_execute(
        "DELETE FROM logs_admin WHERE date_action < datetime('now', ?)",
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

    rowcount = db_execute(
        """
        DELETE FROM paiements_attente
        WHERE statut != 'en_attente'
        AND date_validation < datetime('now', ?)
        """,
        params=[f"-{jours} days"],
        db_context={"table": "paiements_attente", "operation": "cleanup"},
    )
    if rowcount is None:
        return 0
    log_info(f"{rowcount} paiements de plus de {jours}j supprimés.", "DATABASE")
    return rowcount
