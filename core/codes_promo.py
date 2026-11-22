# core/codes_promo.py
"""
Gestion unifiée des codes promo (table unique : codes_promo).

Un code promo combine :
- une réduction commerciale (pourcentage / fixe) — informative, affichée à l'utilisateur
- des jours Premium réellement accordés à l'utilisation

Toutes les opérations sont atomiques (UPDATE conditionnel) pour éviter
les dépassements de limite en cas d'utilisation concurrente.
"""

from users.db import db_execute, db_fetchone, get_connection
from core.utils.logs import log_info, log_error, log_warning


# =========================================================
# SCHÉMA
# =========================================================
def _assurer_table_codes_promo():
    """Crée la table codes_promo et ses colonnes manquantes si besoin.

    Cette fonction est idempotente : elle peut être appelée à chaque requête
    sans effet de bord. Les colonnes ajoutées après coup (migrations) sont
    gérées via ALTER TABLE conditionnel.
    """
    try:
        conn = get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS codes_promo (
                    code TEXT PRIMARY KEY,
                    type_reduction TEXT,
                    valeur REAL,
                    limite_utilisation INTEGER DEFAULT 0,
                    deja_utilise INTEGER DEFAULT 0,
                    jours_premium INTEGER DEFAULT 1,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

            # Migration : ajouter jours_premium si la table existait déjà sans.
            try:
                cur = conn.execute("PRAGMA table_info(codes_promo)")
                colonnes = {row[1] for row in cur.fetchall()}
                if "jours_premium" not in colonnes:
                    conn.execute(
                        "ALTER TABLE codes_promo ADD COLUMN jours_premium INTEGER DEFAULT 1"
                    )
                    conn.commit()
                    log_info(
                        "Colonne jours_premium ajoutée à codes_promo",
                        "CODES_PROMO",
                    )
            except Exception as e:
                log_warning(
                    message="Impossible de vérifier/ajouter jours_premium",
                    module="CODES_PROMO",
                    exception=e,
                )
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        log_error(
            message="Impossible d'assurer la table codes_promo",
            module="CODES_PROMO",
            exception=e,
        )


# =========================================================
# CRÉATION
# =========================================================
def creer_code_promo(code, type_reduction, valeur, limite_utilisation=0, jours_premium=1):
    """Crée un nouveau code promo.

    Retourne True si le code a été créé, False si :
    - paramètres invalides
    - code déjà existant
    - erreur DB
    """
    _assurer_table_codes_promo()

    code = (code or "").strip().upper()
    if not code:
        log_error("Code promo vide", "CODES_PROMO")
        return False
    if type_reduction not in ("pourcentage", "fixe"):
        log_error(f"Type de réduction invalide : {type_reduction}", "CODES_PROMO")
        return False
    try:
        valeur = float(valeur)
        limite_utilisation = int(limite_utilisation or 0)
        jours_premium = int(jours_premium or 1)
    except (TypeError, ValueError):
        log_error("Valeur/limite/jours invalides", "CODES_PROMO")
        return False

    if valeur <= 0:
        log_error(f"Valeur invalide : {valeur}", "CODES_PROMO")
        return False
    if jours_premium <= 0:
        log_error(f"jours_premium invalide : {jours_premium}", "CODES_PROMO")
        return False

    rowcount = db_execute(
        """
        INSERT INTO codes_promo
            (code, type_reduction, valeur, limite_utilisation, jours_premium)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (code) DO NOTHING
        """,
        params=[code, type_reduction, valeur, limite_utilisation, jours_premium],
        db_context={"table": "codes_promo", "operation": "insert"},
    )

    # db_execute retourne None en cas d'erreur DB, 0 si conflit (déjà existant).
    if rowcount is None:
        log_error(f"Échec de création du code {code}", "CODES_PROMO")
        return False
    if rowcount == 0:
        log_warning(f"Code {code} déjà existant", "CODES_PROMO")
        return False

    log_info(
        f"Code promo créé : {code} ({type_reduction} {valeur}, "
        f"{jours_premium}j, limite={limite_utilisation or 'illimitée'})",
        "CODES_PROMO",
    )
    return True


# =========================================================
# VALIDATION (lecture seule, pour affichage)
# =========================================================
def get_code_promo(code):
    """Retourne les infos d'un code (dict) ou None s'il n'existe pas."""
    _assurer_table_codes_promo()
    code = (code or "").strip().upper()
    if not code:
        return None

    row = db_fetchone(
        "SELECT type_reduction, valeur, limite_utilisation, deja_utilise, jours_premium "
        "FROM codes_promo WHERE code = ?",
        params=[code],
        db_context={"table": "codes_promo", "operation": "select"},
    )
    if not row:
        return None

    type_reduction, valeur, limite, deja_utilise, jours_premium = row
    return {
        "code": code,
        "type_reduction": type_reduction,
        "valeur": valeur,
        "limite_utilisation": limite,
        "deja_utilise": deja_utilise,
        "jours_premium": jours_premium or 1,
        "disponible": (limite == 0) or (deja_utilise < limite),
    }


# =========================================================
# UTILISATION (atomique)
# =========================================================
def valider_code_promo(code, user_id):
    """Valide et consomme un code promo de façon atomique.

    Retourne un dict :
    - valide : bool
    - type_reduction, valeur, jours_premium : si valide
    - message : explication (toujours présente)

    L'incrément de deja_utilise est conditionnel (limite_utilisation = 0
    ou deja_utilise < limite_utilisation). En cas de course, un seul
    utilisateur verra valide=True.
    """
    _assurer_table_codes_promo()

    code = (code or "").strip().upper()
    if not code:
        return {"valide": False, "message": "Code invalide."}

    # 1. UPDATE atomique : incrémente uniquement si le code est encore disponible.
    rowcount = db_execute(
        """
        UPDATE codes_promo
        SET deja_utilise = deja_utilise + 1
        WHERE code = ?
          AND (limite_utilisation = 0 OR deja_utilise < limite_utilisation)
        """,
        params=[code],
        db_context={"table": "codes_promo", "operation": "consume"},
    )

    if rowcount is None:
        return {"valide": False, "message": "Erreur technique. Réessaie."}

    if rowcount == 0:
        # Soit le code n'existe pas, soit il est épuisé. On distingue.
        infos = get_code_promo(code)
        if infos is None:
            return {"valide": False, "message": "Code introuvable."}
        return {"valide": False, "message": "Code épuisé."}

    # 2. On relit les infos (après incrément réussi) pour retourner les jours.
    infos = get_code_promo(code)
    if infos is None:
        # Ne devrait jamais arriver (le code vient d'être consommé), mais on
        # protège : on ne peut pas accorder de jours sans métadonnées.
        log_error(
            message="Code consommé mais introuvable en relecture",
            module="CODES_PROMO",
            user_context={"user_id": user_id},
            extra={"code": code},
        )
        return {"valide": False, "message": "Erreur technique. Contacte l'admin."}

    log_info(
        f"Code {code} validé pour user {user_id} "
        f"(+{infos['jours_premium']}j)",
        "CODES_PROMO",
        user_context={"user_id": user_id},
        extra={"code": code, "jours": infos["jours_premium"]},
    )

    return {
        "valide": True,
        "type_reduction": infos["type_reduction"],
        "valeur": infos["valeur"],
        "jours_premium": infos["jours_premium"],
        "message": "Code valide.",
    }


# =========================================================
# RESTITUTION APRÈS ÉCHEC DE CRÉDIT
# =========================================================
def annuler_utilisation_promo(code):
    """Rend une utilisation consommée par valider_code_promo.

    À appeler seulement si les jours Premium n'ont pas été accordés
    (échec technique ou crédit déjà appliqué pour cet utilisateur).
    Ne descend jamais sous 0. Retourne True si la restitution a réussi.
    """
    code = (code or "").strip().upper()
    rowcount = db_execute(
        "UPDATE codes_promo SET deja_utilise = deja_utilise - 1 "
        "WHERE code = ? AND deja_utilise > 0",
        params=[code],
        db_context={"table": "codes_promo", "operation": "annuler"},
    )
    if rowcount is None or rowcount == 0:
        log_error(
            message="Impossible de restituer une utilisation de code promo",
            module="CODES_PROMO",
            extra={"code": code},
        )
        return False
    log_info(f"Utilisation du code {code} restituée", "CODES_PROMO", extra={"code": code})
    return True
