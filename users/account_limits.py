# users/account_limits.py
"""
Gestion des compteurs et limites de pronostics.
- Compteur atomique (ON CONFLICT DO UPDATE)
- Réservation atomique AVANT calcul (reserver_pronostic) : la limite est
  vérifiée dans la même requête SQL que l'incrément, donc pas de dépassement
  même avec des demandes simultanées.
- Remboursement si le calcul échoue (annuler_pronostic)
- Limites dynamiques (paramètres BDD)
- Logs enrichis
"""

from datetime import datetime

from users.db import db_execute, db_fetchone, db_fetchone_strict
from users.account_base import est_premium
from core.utils.logs import log_info, log_error, log_warning


def _date_kinshasa_str():
    """Retourne la date du jour en Kinshasa (UTC+1) au format YYYY-MM-DD."""
    from datetime import timezone, timedelta
    tz = timezone(timedelta(hours=1))
    return datetime.now(tz).strftime("%Y-%m-%d")


def incrementer_compteur(user_id):
    """Incrémente le compteur de pronostics du jour (atomique).

    Conservé pour compatibilité. Le flux de pronostic utilise désormais
    reserver_pronostic(), qui applique la limite au moment de l'incrément.
    """
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour incrementer_compteur",
            module="ACCOUNTS",
            extra={"user_id": user_id},
        )
        return False

    today = _date_kinshasa_str()
    rowcount = db_execute(
        """
        INSERT INTO compteurs_jour (user_id, date, compteur)
        VALUES (?, ?, 1)
        ON CONFLICT (user_id, date)
        DO UPDATE SET compteur = compteurs_jour.compteur + 1
        """,
        params=[user_id, today],
        db_context={"table": "compteurs_jour", "operation": "increment"},
    )
    return rowcount is not None


def reserver_pronostic(user_id):
    """Réserve atomiquement une place de pronostic pour aujourd'hui.

    À appeler AVANT le calcul. La condition « compteur < limite » fait partie
    de la même requête SQL que l'incrément : deux demandes simultanées ne
    peuvent pas dépasser la limite.

    Retourne True si la place est réservée. Retourne False si la limite est
    atteinte, si les paramètres sont invalides, ou si la base est injoignable
    (on refuse par sécurité : fail-closed).
    """
    if not isinstance(user_id, int):
        return False

    limite = get_limite_jour(user_id)
    if not isinstance(limite, int) or limite <= 0:
        return False

    today = _date_kinshasa_str()
    rowcount = db_execute(
        """
        INSERT INTO compteurs_jour (user_id, date, compteur)
        VALUES (?, ?, 1)
        ON CONFLICT (user_id, date)
        DO UPDATE SET compteur = compteurs_jour.compteur + 1
        WHERE compteurs_jour.compteur < ?
        """,
        params=[user_id, today, limite],
        db_context={"table": "compteurs_jour", "operation": "reserve"},
    )
    # rowcount == 1 : place réservée ; 0 : limite atteinte ; None : erreur DB
    return bool(rowcount)


def annuler_pronostic(user_id):
    """Rend une place réservée (ex. : le calcul a échoué).

    Ne descend jamais sous 0. Retourne True si l'opération a réussi en base.
    """
    if not isinstance(user_id, int):
        return False

    today = _date_kinshasa_str()
    rowcount = db_execute(
        "UPDATE compteurs_jour SET compteur = compteur - 1 "
        "WHERE user_id = ? AND date = ? AND compteur > 0",
        params=[user_id, today],
        db_context={"table": "compteurs_jour", "operation": "release"},
    )
    return rowcount is not None


def get_compteur_jour(user_id):
    """Récupère le compteur du jour."""
    today = _date_kinshasa_str()
    row = db_fetchone(
        "SELECT compteur FROM compteurs_jour WHERE user_id = ? AND date = ?",
        params=[user_id, today],
        db_context={"table": "compteurs_jour", "operation": "read"},
    )
    return row[0] if row else 0


def get_compteur_jour_strict(user_id):
    """Comme get_compteur_jour, mais lève DatabaseError si la base est en erreur.

    Utilisé par peut_faire_pronostic : une panne ne doit pas passer pour 0 pronostic.
    """
    today = _date_kinshasa_str()
    row = db_fetchone_strict(
        "SELECT compteur FROM compteurs_jour WHERE user_id = ? AND date = ?",
        params=[user_id, today],
        db_context={"table": "compteurs_jour", "operation": "read_strict"},
    )
    return row[0] if row else 0


def get_limite_jour(user_id):
    """Retourne la limite quotidienne selon le statut."""
    from config import LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR

    try:
        if est_premium(user_id):
            return LIMITE_PREMIUM_JOUR
    except Exception as e:
        log_warning(
            message="Impossible de vérifier le statut premium, fallback FREE",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            exception=e,
        )

    # Récupération du paramètre dynamique
    from users.admin import get_parametre
    limite_bdd = get_parametre("limite_free", str(LIMITE_FREE_JOUR))
    try:
        return int(limite_bdd)
    except (ValueError, TypeError):
        log_warning(
            message="Paramètre 'limite_free' invalide, fallback constante",
            module="ACCOUNTS",
            extra={"valeur_recue": str(limite_bdd)},
        )
        return LIMITE_FREE_JOUR


def peut_faire_pronostic(user_id):
    """Vérification indicative (affichage du menu).

    La décision réelle est prise par reserver_pronostic() au moment du calcul.
    """
    try:
        compteur = get_compteur_jour_strict(user_id)
        limite = get_limite_jour(user_id)
        return compteur < limite
    except Exception as e:
        log_error(
            message="Impossible de vérifier si l'utilisateur peut faire un pronostic",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            exception=e,
        )
        return False
