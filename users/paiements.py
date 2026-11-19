# users/paiements.py
"""
Gestion des demandes de paiement et codes Premium.
- Opérations atomiques (UPDATE ... WHERE statut='en_attente')
- Détection des race conditions via rowcount
- Logs enrichis
"""

import random
import string

from users.db import db_execute, db_fetchone, db_fetchall, db_fetchone_dict
from core.utils.logs import log_info, log_error, log_warning


# =========================================================
# DEMANDES DE PAIEMENT
# =========================================================
def creer_demande_paiement(user_id, abonnement, montant, preuve_photo_id):
    """Crée une demande de paiement en attente. Retourne l'ID ou None."""
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour creer_demande_paiement",
            module="PAIEMENTS",
            extra={"user_id": user_id},
        )
        return None

    try:
        from users.db import get_connection
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO paiements_attente
                (user_id, abonnement, montant, preuve_photo_id)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, abonnement, montant, preuve_photo_id),
            )
            conn.commit()
            row = conn.execute("SELECT last_insert_rowid()").fetchone()
            demande_id = row[0] if row else None
            log_info(
                f"Demande paiement #{demande_id} créée",
                "PAIEMENTS",
                user_context={"user_id": user_id},
                extra={"abonnement": abonnement, "montant": montant},
            )
            return demande_id
        finally:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion (creer_demande)",
                    module="PAIEMENTS",
                    exception=e,
                )
    except Exception as e:
        log_error(
            message="Impossible de créer la demande de paiement",
            module="PAIEMENTS",
            user_context={"user_id": user_id},
            extra={"abonnement": abonnement, "montant": montant},
            exception=e,
        )
        return None


def get_demande(demande_id):
    """Récupère une demande par ID."""
    return db_fetchone_dict(
        "SELECT * FROM paiements_attente WHERE id = ?",
        params=[demande_id],
        db_context={"table": "paiements_attente", "operation": "get"},
    )


def get_demandes_en_attente(limite=20):
    """Récupère les demandes en attente."""
    from users.db import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(
            """
            SELECT * FROM paiements_attente
            WHERE statut = 'en_attente'
            ORDER BY date_demande DESC
            LIMIT ?
            """,
            (limite,),
        )
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        log_error(
            message="Impossible de récupérer les demandes en attente",
            module="PAIEMENTS",
            exception=e,
        )
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def valider_demande(demande_id, admin_id):
    """
    Valide une demande de paiement.
    ATOMIQUE : ne valide que si statut='en_attente'.
    Retourne True si la validation a eu lieu, False si déjà traité ou échec.
    """
    if not isinstance(demande_id, int) or not isinstance(admin_id, int):
        log_warning(
            message="Paramètres invalides pour valider_demande",
            module="PAIEMENTS",
            extra={"demande_id": demande_id, "admin_id": admin_id},
        )
        return False

    rowcount = db_execute(
        """
        UPDATE paiements_attente
        SET statut = 'valide', date_validation = CURRENT_TIMESTAMP, admin_id = ?
        WHERE id = ? AND statut = 'en_attente'
        """,
        params=[admin_id, demande_id],
        db_context={"table": "paiements_attente", "operation": "valider"},
    )

    if rowcount is None or rowcount == 0:
        log_warning(
            message="Validation impossible (déjà traitée ou inexistante)",
            module="PAIEMENTS",
            extra={"demande_id": demande_id, "admin_id": admin_id},
        )
        return False

    log_info(
        f"Demande #{demande_id} validée par admin {admin_id}",
        "PAIEMENTS",
        extra={"demande_id": demande_id, "admin_id": admin_id},
    )
    return True


def refuser_demande(demande_id, admin_id):
    """Refuse une demande (atomique)."""
    if not isinstance(demande_id, int) or not isinstance(admin_id, int):
        log_warning(
            message="Paramètres invalides pour refuser_demande",
            module="PAIEMENTS",
            extra={"demande_id": demande_id, "admin_id": admin_id},
        )
        return False

    rowcount = db_execute(
        """
        UPDATE paiements_attente
        SET statut = 'refuse', date_validation = CURRENT_TIMESTAMP, admin_id = ?
        WHERE id = ? AND statut = 'en_attente'
        """,
        params=[admin_id, demande_id],
        db_context={"table": "paiements_attente", "operation": "refuser"},
    )

    if rowcount is None or rowcount == 0:
        log_warning(
            message="Refus impossible (déjà traité ou inexistant)",
            module="PAIEMENTS",
            extra={"demande_id": demande_id, "admin_id": admin_id},
        )
        return False

    log_info(
        f"Demande #{demande_id} refusée par admin {admin_id}",
        "PAIEMENTS",
        extra={"demande_id": demande_id, "admin_id": admin_id},
    )
    return True


def compter_demandes_en_attente():
    """Compte les demandes en attente."""
    row = db_fetchone(
        "SELECT COUNT(*) FROM paiements_attente WHERE statut = 'en_attente'",
        db_context={"table": "paiements_attente", "operation": "count"},
    )
    return row[0] if row else 0


# =========================================================
# CODES PREMIUM
# =========================================================
def _generer_code_unique(conn, jours, prefix="PREM", max_tentatives=10):
    """Génère un code unique (INSERT ... ON CONFLICT DO NOTHING atomique)."""
    for tentative in range(max_tentatives):
        code = f"{prefix}-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        try:
            cur = conn.execute(
                """
                INSERT INTO codes_premium (code, jours)
                VALUES (?, ?)
                ON CONFLICT (code) DO NOTHING
                """,
                (code, jours),
            )
            rowcount = cur.rowcount if hasattr(cur, "rowcount") else 0
            if rowcount and rowcount > 0:
                return code
            # Collision : on réessaie
            log_warning(
                message=f"Collision de code (tentative {tentative + 1}/{max_tentatives})",
                module="PAIEMENTS",
                extra={"code_preview": code[:10]},
            )
        except Exception as e:
            log_error(
                message=f"Erreur INSERT code (tentative {tentative + 1})",
                module="PAIEMENTS",
                exception=e,
            )
    return None


def generer_code(jours, prefix="PREM"):
    """Génère un code Premium unique."""
    if not isinstance(jours, int) or jours <= 0:
        log_warning(
            message="Durée invalide pour generer_code",
            module="PAIEMENTS",
            extra={"jours": jours},
        )
        return None

    from users.db import get_connection
    conn = None
    try:
        conn = get_connection()
        code = _generer_code_unique(conn, jours, prefix)
        if code:
            conn.commit()
            log_info(
                f"Code généré pour {jours}j",
                "PAIEMENTS",
                extra={"code": code, "jours": jours},
            )
        return code
    except Exception as e:
        log_error(
            message="Erreur lors de la génération de code",
            module="PAIEMENTS",
            extra={"jours": jours},
            exception=e,
        )
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                log_warning(
                    message="Impossible de fermer la connexion (generer_code)",
                    module="PAIEMENTS",
                    exception=e,
                )


def generer_lot_codes(jours, quantite):
    """Génère un lot de codes."""
    if not isinstance(quantite, int) or quantite <= 0 or quantite > 100:
        log_warning(
            message="Quantité invalide pour generer_lot_codes",
            module="PAIEMENTS",
            extra={"quantite": quantite},
        )
        return []

    codes = []
    for _ in range(quantite):
        code = generer_code(jours)
        if code:
            codes.append(code)

    log_info(
        f"{len(codes)}/{quantite} codes générés pour {jours}j",
        "PAIEMENTS",
        extra={"jours": jours, "demande": quantite, "succes": len(codes)},
    )
    return codes


def utiliser_code(code, user_id):
    """
    Utilise un code Premium (table codes_premium, format PREM-XXXXXXXX).

    Cette fonction gère UNIQUEMENT les codes "premium" générés par
    generer_code() (table codes_premium). Les codes promo manuels
    (/codepromo) sont gérés par core.codes_promo.

    Retourne {"jours": N} si succès, {"erreur": "..."} sinon.
    """
    if not code or not isinstance(code, str):
        return {"erreur": "Code invalide"}

    code = code.strip().upper()

    # 1. Vérification préliminaire (lecture seule)
    row = db_fetchone(
        "SELECT jours, utilise FROM codes_premium WHERE code = ?",
        params=[code],
        db_context={"table": "codes_premium", "operation": "check"},
    )

    if not row:
        log_warning(
            message="Code Premium introuvable",
            module="PAIEMENTS",
            user_context={"user_id": user_id},
            extra={"code": code},
        )
        return {"erreur": "Code introuvable"}

    jours, utilise = row
    if utilise:
        log_warning(
            message="Code Premium déjà utilisé (vérif préliminaire)",
            module="PAIEMENTS",
            user_context={"user_id": user_id},
            extra={"code": code},
        )
        return {"erreur": "Code déjà utilisé"}

    # 2. UPDATE atomique : ne marque utilisé que si utilise=0
    rowcount = db_execute(
        """
        UPDATE codes_premium
        SET utilise = 1, utilise_par = ?, date_utilisation = CURRENT_TIMESTAMP
        WHERE code = ? AND utilise = 0
        """,
        params=[user_id, code],
        db_context={"table": "codes_premium", "operation": "utiliser"},
    )

    if rowcount is None:
        log_error(
            message="Erreur DB lors de l'utilisation du code",
            module="PAIEMENTS",
            user_context={"user_id": user_id},
            extra={"code": code},
        )
        return {"erreur": "Erreur technique. Réessaie."}

    if rowcount == 0:
        # Race condition : un autre utilisateur a utilisé le code entre-temps
        log_warning(
            message="Code Premium déjà utilisé (race condition)",
            module="PAIEMENTS",
            user_context={"user_id": user_id},
            extra={"code": code},
        )
        return {"erreur": "Code déjà utilisé"}

    log_info(
        f"Code Premium utilisé : +{jours}j pour {user_id}",
        "PAIEMENTS",
        user_context={"user_id": user_id},
        extra={"code": code, "jours": jours},
    )
    return {"jours": jours}


def get_codes_disponibles(limite=50):
    """Récupère les codes non utilisés."""
    from users.db import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(
            """
            SELECT * FROM codes_premium
            WHERE utilise = 0
            ORDER BY date_creation DESC
            LIMIT ?
            """,
            (limite,),
        )
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        log_error(
            message="Impossible de récupérer les codes disponibles",
            module="PAIEMENTS",
            exception=e,
        )
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def get_codes_utilises(limite=50):
    """Récupère les codes utilisés."""
    from users.db import get_connection
    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(
            """
            SELECT * FROM codes_premium
            WHERE utilise = 1
            ORDER BY date_utilisation DESC
            LIMIT ?
            """,
            (limite,),
        )
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        log_error(
            message="Impossible de récupérer les codes utilisés",
            module="PAIEMENTS",
            exception=e,
        )
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def compter_codes_disponibles():
    """Compte les codes non utilisés."""
    row = db_fetchone(
        "SELECT COUNT(*) FROM codes_premium WHERE utilise = 0",
        db_context={"table": "codes_premium", "operation": "count"},
    )
    return row[0] if row else 0
