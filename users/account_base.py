# users/account_base.py
"""
Gestion de base des comptes utilisateurs.
- set_premium et ajouter_jours_premium sont UNIFIÉS (cumulables)
- Parsing de dates robuste (multi-format)
- Logs enrichis avec contexte utilisateur
"""

from datetime import datetime, timedelta

from users.db import (
    db_execute, db_fetchall, db_fetchone, db_fetchone_dict,
    db_fetchone_strict, DatabaseError,
)
from core.utils.logs import log_info, log_error, log_warning


# =========================================================
# PARSING DE DATES ROBUSTE
# =========================================================
_FORMATS_DATE = [
    "%Y-%m-%d %H:%M:%S.%f",   # 2026-11-20 20:38:00.123456
    "%Y-%m-%d %H:%M:%S",      # 2026-11-20 20:38:00
    "%Y-%m-%d %H:%M",         # 2026-11-20 20:38
    "%Y-%m-%dT%H:%M:%S",      # 2026-11-20T20:38:00
    "%Y-%m-%dT%H:%M:%S.%f",   # 2026-11-20T20:38:00.123456
    "%Y-%m-%d",               # 2026-11-20
]


def _parser_date(date_str):
    """
    Parse une date au format string vers datetime.
    Retourne None si aucun format ne fonctionne.
    """
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    try:
        for fmt in _FORMATS_DATE:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
    except Exception as e:
        log_warning(
            message="Impossible de parser une date",
            module="ACCOUNTS",
            extra={"date_str": str(date_str)[:50]},
            exception=e,
        )
    return None


# =========================================================
# LECTURE UTILISATEUR
# =========================================================
def utilisateur_existe(user_id):
    """Vérifie si un utilisateur existe."""
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour utilisateur_existe",
            module="ACCOUNTS",
            extra={"user_id": user_id},
        )
        return False
    row = db_fetchone(
        "SELECT 1 FROM utilisateurs WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "utilisateurs", "operation": "exists"},
    )
    return row is not None


def get_user_info(user_id):
    """Récupère toutes les infos d'un utilisateur sous forme de dict."""
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour get_user_info",
            module="ACCOUNTS",
            extra={"user_id": user_id},
        )
        return None
    return db_fetchone_dict(
        "SELECT * FROM utilisateurs WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "utilisateurs", "operation": "read"},
    )


def get_user_status(user_id):
    """Retourne (status, date_expiration) ou ('free', None)."""
    info = get_user_info(user_id)
    if not info:
        return "free", None
    return info.get("status", "free"), info.get("date_expiration")


def _lire_info_strict(user_id):
    """Lit les champs utiles d'un utilisateur. Lève DatabaseError en cas de panne.

    Contrairement à get_user_info (qui renvoie None en cas d'erreur), cette
    fonction permet de distinguer « utilisateur introuvable » et « base en panne »
    avant une écriture.
    """
    row = db_fetchone_strict(
        "SELECT status, date_expiration, first_name FROM utilisateurs WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "utilisateurs", "operation": "read_strict"},
    )
    if row is None:
        return None
    return {"status": row[0] or "free", "date_expiration": row[1], "first_name": row[2]}


# =========================================================
# ENREGISTREMENT
# =========================================================
def enregistrer_utilisateur(user_id, username, first_name):
    """
    Enregistre un nouvel utilisateur (idempotent).
    Retourne True si créé, False si déjà existant ou échec.
    """
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour enregistrer_utilisateur",
            module="ACCOUNTS",
            extra={"user_id": user_id},
        )
        return False

    if utilisateur_existe(user_id):
        return False

    rowcount = db_execute(
        """
        INSERT INTO utilisateurs (user_id, username, first_name, status)
        VALUES (?, ?, ?, 'free')
        ON CONFLICT (user_id) DO NOTHING
        """,
        params=[user_id, username or "", first_name or ""],
        db_context={"table": "utilisateurs", "operation": "insert"},
    )
    if rowcount and rowcount > 0:
        log_info(
            f"Nouvel utilisateur enregistré : {first_name} ({user_id})",
            "ACCOUNTS",
            user_context={"user_id": user_id, "user_name": first_name, "username": username},
        )
        return True
    return False


# =========================================================
# GESTION PREMIUM (UNIFIÉE)
# =========================================================
def _calculer_nouvelle_expiration(expiration_actuelle, status_actuel, jours_a_ajouter):
    """
    Calcule la nouvelle date d'expiration :
    - Si l'utilisateur est encore Premium et sa date est dans le futur :
      on ajoute les jours à la date existante (cumul)
    - Sinon : on part de maintenant + jours
    """
    maintenant = datetime.now()
    expiration_dt = _parser_date(expiration_actuelle)

    if status_actuel == "premium" and expiration_dt and expiration_dt > maintenant:
        return expiration_dt + timedelta(days=jours_a_ajouter)
    return maintenant + timedelta(days=jours_a_ajouter)


def ajouter_jours_premium(user_id, jours):
    """
    Ajoute X jours de Premium à un utilisateur (cumulable).
    Remplace set_premium dans la majorité des cas.
    Retourne True si succès, False sinon.
    """
    if not isinstance(user_id, int) or not isinstance(jours, int) or jours <= 0:
        log_warning(
            message="Paramètres invalides pour ajouter_jours_premium",
            module="ACCOUNTS",
            extra={"user_id": user_id, "jours": jours},
        )
        return False

    try:
        info = _lire_info_strict(user_id)
    except DatabaseError:
        # Panne DB : on n'écrit rien, le crédit sera libéré et pourra être réessayé
        return False
    if not info:
        log_error(
            message="Impossible d'ajouter du premium : utilisateur introuvable",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            extra={"jours_demandes": jours},
        )
        return False

    expiration_actuelle = info.get("date_expiration")
    status_actuel = info.get("status", "free")

    nouvelle_date = _calculer_nouvelle_expiration(
        expiration_actuelle, status_actuel, jours
    )
    nouvelle_date_str = nouvelle_date.strftime("%Y-%m-%d %H:%M:%S")

    rowcount = db_execute(
        """
        UPDATE utilisateurs
        SET status = 'premium', date_expiration = ?
        WHERE user_id = ?
        """,
        params=[nouvelle_date_str, user_id],
        db_context={"table": "utilisateurs", "operation": "add_premium"},
    )

    if rowcount is None or rowcount == 0:
        log_error(
            message="Échec de la mise à jour premium (0 ligne affectée)",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            extra={"jours": jours, "nouvelle_date": nouvelle_date_str},
        )
        return False

    log_info(
        f"+{jours}j Premium pour {user_id} (expire {nouvelle_date_str})",
        "ACCOUNTS",
        user_context={"user_id": user_id, "user_name": info.get("first_name")},
        extra={"ancienne": expiration_actuelle, "nouvelle": nouvelle_date_str},
    )
    return True


def set_premium(user_id, date_expiration):
    """
    Définit une date d'expiration absolue (admin only).
    ⚠️ Remplace la date existante, ne cumule PAS.
    Préférer ajouter_jours_premium pour les ajouts.
    """
    if not isinstance(user_id, int):
        log_warning(
            message="user_id invalide pour set_premium",
            module="ACCOUNTS",
            extra={"user_id": user_id},
        )
        return False

    if isinstance(date_expiration, datetime):
        date_expiration = date_expiration.strftime("%Y-%m-%d %H:%M:%S")
    else:
        parsed = _parser_date(date_expiration)
        if not parsed:
            log_error(
                message="Date d'expiration invalide pour set_premium",
                module="ACCOUNTS",
                user_context={"user_id": user_id},
                extra={"date_recue": str(date_expiration)},
            )
            return False
        date_expiration = parsed.strftime("%Y-%m-%d %H:%M:%S")

    try:
        info = _lire_info_strict(user_id)
    except DatabaseError:
        return False
    if not info:
        log_error(
            message="Impossible de définir premium : utilisateur introuvable",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            extra={"date_demandee": date_expiration},
        )
        return False

    rowcount = db_execute(
        """
        UPDATE utilisateurs
        SET status = 'premium', date_expiration = ?
        WHERE user_id = ?
        """,
        params=[date_expiration, user_id],
        db_context={"table": "utilisateurs", "operation": "set_premium"},
    )

    if rowcount is None or rowcount == 0:
        return False

    log_info(
        f"Utilisateur {user_id} passé en PREMIUM (expire {date_expiration})",
        "ACCOUNTS",
        user_context={"user_id": user_id},
        extra={"ancienne": info.get("date_expiration"), "nouvelle": date_expiration},
    )
    return True


def est_premium(user_id):
    """Vérifie si un utilisateur est Premium (parsing robuste)."""
    status, expiration = get_user_status(user_id)
    if status != "premium" or not expiration:
        return False

    expiration_dt = _parser_date(expiration)
    if expiration_dt is None:
        log_warning(
            message="Format de date d'expiration invalide",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            extra={"date_expiration": str(expiration)},
        )
        return False

    return expiration_dt > datetime.now()


def expirer_premiums():
    """
    Repasse en 'free' les comptes premium dont l'abonnement est terminé.

    Le filtrage est fait en Python via _parser_date (et non en SQL) car les
    dates sont stockées en texte multi-format : une comparaison lexicographique
    ferait expirer à tort '2026-11-20' face à '2026-11-20 08:00:00'.

    Une date_expiration NULL est traitée comme expirée, ce qui est cohérent
    avec est_premium qui renvoie False sans date.

    Retourne le nombre de comptes basculés en 'free'.
    """
    rows = db_fetchall(
        "SELECT user_id, date_expiration FROM utilisateurs WHERE status = 'premium'"
    )
    if not rows:
        return 0

    maintenant = datetime.now()
    expires = []
    for row in rows:
        user_id = row[0]
        expiration = row[1] if len(row) > 1 else None
        expiration_dt = _parser_date(expiration)
        if expiration_dt is None or expiration_dt <= maintenant:
            expires.append(user_id)

    bascules = 0
    for user_id in expires:
        rowcount = db_execute(
            "UPDATE utilisateurs SET status = 'free' WHERE user_id = ?",
            params=[user_id],
            db_context={"table": "utilisateurs", "operation": "expire_premium"},
        )
        if rowcount and rowcount > 0:
            bascules += 1

    if bascules > 0:
        log_info(
            f"{bascules} abonnement(s) premium expiré(s) repassé(s) en free",
            "ACCOUNTS",
            extra={"nb_bascules": bascules},
        )
    return bascules


def get_statut_label(user_id):
    """Retourne 'PREMIUM' ou 'FREE'."""
    return "PREMIUM" if est_premium(user_id) else "FREE"


# =========================================================
# LANGUE
# =========================================================
def get_langue(user_id):
    """Récupère la langue d'un utilisateur (fallback 'fr')."""
    row = db_fetchone(
        "SELECT langue FROM utilisateurs WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "utilisateurs", "operation": "get_langue"},
    )
    if row and row[0]:
        return row[0]
    return "fr"


def set_langue(user_id, langue):
    """Change la langue d'un utilisateur.

    Les langues valides sont lues depuis core.translations.LANGUES_DISPONIBLES
    (source unique de vérité) — plus de hardcode ici.
    """
    # Import local pour éviter un cycle au chargement du module
    from core.translations import LANGUES_DISPONIBLES

    if langue not in LANGUES_DISPONIBLES:
        log_warning(
            message="Langue non supportée",
            module="ACCOUNTS",
            user_context={"user_id": user_id},
            extra={
                "langue_demandee": langue,
                "langues_valides": list(LANGUES_DISPONIBLES.keys()),
            },
        )
        return False

    rowcount = db_execute(
        "UPDATE utilisateurs SET langue = ? WHERE user_id = ?",
        params=[langue, user_id],
        db_context={"table": "utilisateurs", "operation": "set_langue"},
    )
    return rowcount is not None and rowcount > 0
