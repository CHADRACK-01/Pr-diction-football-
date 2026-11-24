# users/credits.py
"""
Crédits de jours Premium, idempotents.

Chaque crédit a une RÉFÉRENCE unique (ex. "paiement:42", "code:PREM-XXXX",
"parrainage:123"). Un même crédit ne peut être appliqué qu'une seule fois,
même si la demande est répétée ou faite en parallèle.

Principe : on réserve la référence AVANT d'ajouter les jours. Si l'ajout
échoue, la réservation est libérée pour permettre une nouvelle tentative.
"""
from users.database import db_execute, db_fetchone
from core.utils.logs import log_error, log_info

_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS credits_premium (
        reference TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        jours INTEGER NOT NULL,
        source TEXT,
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""


def _assurer_table():
    db_execute(_TABLE_SQL, db_context={"table": "credits_premium", "operation": "create"})


def deja_credite(reference):
    """True si cette référence a déjà été créditée."""
    _assurer_table()
    row = db_fetchone(
        "SELECT 1 FROM credits_premium WHERE reference = ?",
        params=[reference],
        db_context={"table": "credits_premium", "operation": "check"},
    )
    return row is not None


def crediter_premium(reference, user_id, jours, source="inconnue"):
    """Crédite `jours` une seule fois pour `reference`.

    Retourne :
      "ok"    : crédit appliqué maintenant
      "deja"  : déjà crédité auparavant (rien n'a été ajouté)
      "echec" : impossible (paramètres invalides, base ou ajout en erreur)
    """
    if not reference or not isinstance(user_id, int) or not isinstance(jours, int) or jours <= 0:
        return "echec"

    _assurer_table()

    # 1. Réserver la référence : une seule insertion peut réussir (clé primaire)
    reserve = db_execute(
        "INSERT INTO credits_premium (reference, user_id, jours, source) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(reference) DO NOTHING",
        params=[reference, user_id, jours, source],
        db_context={"table": "credits_premium", "operation": "reserve"},
    )
    if reserve is None:
        return "echec"
    if reserve == 0:
        return "deja"

    # 2. Appliquer le crédit
    from users.account_base import ajouter_jours_premium
    try:
        ok = ajouter_jours_premium(user_id, jours)
    except Exception as e:
        ok = False
        log_error(f"Ajout Premium en erreur ({reference})", "CREDITS", exception=e)

    if not ok:
        # 3. Libérer la réservation : une nouvelle tentative sera possible
        db_execute(
            "DELETE FROM credits_premium WHERE reference = ?",
            params=[reference],
            db_context={"table": "credits_premium", "operation": "release"},
        )
        return "echec"

    log_info(f"Crédit appliqué : +{jours}j pour {user_id} ({reference})", "CREDITS")
    return "ok"
