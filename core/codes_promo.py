# core/codes_promo.py
"""
Fonctionnalité 174 : Gestion des codes promo.
Crée la table si elle n'existe pas, et gère la création/validation des codes.
"""

from users.db import db_execute, db_fetchone
from core.utils.logs import log_info, log_error


def _assurer_table_codes_promo():
    """Crée la table codes_promo si elle n'existe pas."""
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS codes_promo (
            code TEXT PRIMARY KEY,
            type_reduction TEXT,
            valeur REAL,
            limite_utilisation INTEGER DEFAULT 0,
            deja_utilise INTEGER DEFAULT 0,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        db_context={"table": "codes_promo", "operation": "create"}
    )


def creer_code_promo(code, type_reduction, valeur, limite_utilisation=0):
    """Crée un nouveau code promo."""
    _assurer_table_codes_promo()

    code = code.strip().upper()
    if type_reduction not in ("pourcentage", "fixe"):
        log_error(f"Type de réduction invalide : {type_reduction}", "CODES_PROMO")
        return False
    if valeur <= 0:
        log_error(f"Valeur invalide : {valeur}", "CODES_PROMO")
        return False

    rowcount = db_execute(
        """
        INSERT INTO codes_promo (code, type_reduction, valeur, limite_utilisation)
        VALUES (?, ?, ?, ?)
        """,
        params=[code, type_reduction, valeur, limite_utilisation],
        db_context={"table": "codes_promo", "operation": "insert"}
    )

    if rowcount is None:
        log_error(f"Échec de création du code {code}", "CODES_PROMO")
        return False

    log_info(f"Code promo créé : {code} ({type_reduction} {valeur})", "CODES_PROMO")
    return True


def valider_code_promo(code, user_id):
    """Vérifie si un code est valide et l'incrémente de façon atomique."""
    _assurer_table_codes_promo()

    code = code.strip().upper()
    row = db_fetchone(
        "SELECT type_reduction, valeur, limite_utilisation, deja_utilise FROM codes_promo WHERE code = ?",
        params=[code],
        db_context={"table": "codes_promo", "operation": "select"}
    )

    if not row:
        return {"valide": False, "message": "Code introuvable."}

    type_reduction, valeur, limite, deja_utilise = row

    if limite > 0 and deja_utilise >= limite:
        return {"valide": False, "message": "Code épuisé."}

    # Incrément atomique
    rowcount = db_execute(
        """
        UPDATE codes_promo
        SET deja_utilise = deja_utilise + 1
        WHERE code = ? AND (limite_utilisation = 0 OR deja_utilise < limite_utilisation)
        """,
        params=[code],
        db_context={"table": "codes_promo", "operation": "increment"}
    )

    if rowcount is None or rowcount == 0:
        return {"valide": False, "message": "Code épuisé."}

    log_info(f"Code {code} validé pour user {user_id}", "CODES_PROMO")
    return {
        "valide": True,
        "type_reduction": type_reduction,
        "valeur": valeur,
        "message": "Code valide."
    }
