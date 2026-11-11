# core/session.py
"""
Gestion des sessions de pronostic (BDD).
- TTL de 30 min (nettoyage automatique)
- Plus de pollution dans ADMIN_SESSIONS
- Stockage des équipes disponibles (JSON)
"""

import json
from datetime import datetime, timezone, timedelta

from users.db import db_execute, db_fetchone
from core.utils.logs import log_info, log_error, log_warning

TZ_KINSHASA = timezone(timedelta(hours=1))
TTL_MINUTES = 30


def _now_str():
    return datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d %H:%M:%S")


def _nettoyer_sessions_expirees():
    """Supprime les sessions plus vieilles que TTL_MINUTES."""
    seuil = (datetime.now(TZ_KINSHASA) - timedelta(minutes=TTL_MINUTES)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    db_execute(
        "DELETE FROM sessions_pronostic WHERE date_maj < ?",
        params=[seuil],
        db_context={"table": "sessions_pronostic", "operation": "cleanup_expired"},
    )


def creer_session(user_id, competition, nom_competition, equipes):
    """
    Crée/réinitialise une session à l'étape 'domicile'.
    `equipes` est une liste de noms.
    """
    _nettoyer_sessions_expirees()

    try:
        equipes_json = json.dumps(equipes, ensure_ascii=False)
    except Exception as e:
        log_error(
            message="Impossible d'encoder les équipes en JSON",
            module="SESSION",
            user_context={"user_id": user_id},
            exception=e,
        )
        return False

    now = _now_str()
    rowcount = db_execute(
        """
        INSERT INTO sessions_pronostic
        (user_id, competition, etape, equipe_dom, equipe_ext, equipes_dispo,
         date_creation, date_maj)
        VALUES (?, ?, 'domicile', NULL, NULL, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            competition = excluded.competition,
            etape = 'domicile',
            equipe_dom = NULL,
            equipe_ext = NULL,
            equipes_dispo = excluded.equipes_dispo,
            date_creation = excluded.date_creation,
            date_maj = excluded.date_maj
        """,
        params=[user_id, competition, equipes_json, now, now],
        db_context={"table": "sessions_pronostic", "operation": "create"},
    )

    if rowcount is None:
        log_error(
            message="Impossible de créer la session de pronostic",
            module="SESSION",
            user_context={"user_id": user_id},
            extra={"competition": competition},
        )
        return False

    log_info(
        f"Session créée pour {user_id} ({competition}, {len(equipes)} équipes)",
        "SESSION",
        user_context={"user_id": user_id},
    )
    return True


def get_session(user_id):
    """
    Récupère la session active (ou None).
    Retourne un dict : {competition, etape, equipe_dom, equipe_ext, equipes}.
    """
    _nettoyer_sessions_expirees()

    row = db_fetchone(
        """
        SELECT competition, etape, equipe_dom, equipe_ext, equipes_dispo, date_maj
        FROM sessions_pronostic WHERE user_id = ?
        """,
        params=[user_id],
        db_context={"table": "sessions_pronostic", "operation": "get"},
    )
    if not row:
        return None

    competition, etape, equipe_dom, equipe_ext, equipes_json, date_maj = row

    equipes = []
    if equipes_json:
        try:
            equipes = json.loads(equipes_json)
        except Exception as e:
            log_warning(
                message="JSON équipes corrompu, session réinitialisée",
                module="SESSION",
                user_context={"user_id": user_id},
                exception=e,
            )
            clear_session(user_id)
            return None

    return {
        "competition": competition,
        "etape": etape,
        "equipe_dom": equipe_dom,
        "equipe_ext": equipe_ext,
        "equipes": equipes,
    }


def maj_session_etape(user_id, etape, equipe_dom=None, equipe_ext=None):
    """Met à jour l'étape de la session."""
    now = _now_str()
    rowcount = db_execute(
        """
        UPDATE sessions_pronostic
        SET etape = ?, equipe_dom = COALESCE(?, equipe_dom),
            equipe_ext = COALESCE(?, equipe_ext), date_maj = ?
        WHERE user_id = ?
        """,
        params=[etape, equipe_dom, equipe_ext, now, user_id],
        db_context={"table": "sessions_pronostic", "operation": "update_etape"},
    )
    return rowcount is not None and rowcount > 0


def clear_session(user_id):
    """Supprime la session d'un utilisateur."""
    db_execute(
        "DELETE FROM sessions_pronostic WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "sessions_pronostic", "operation": "clear"},
    )


# =========================================================
# COMPATIBILITÉ avec l'ancien code (encore utilisé par certains modules)
# =========================================================
def set_session_competition(user_id, competition):
    """Compatibilité : crée une session minimale sans équipes."""
    return creer_session(user_id, competition, competition, [])


def get_session_competition(user_id):
    """Compatibilité : retourne juste la compétition."""
    s = get_session(user_id)
    return s["competition"] if s else "default"


def clear_session_competition(user_id):
    """Compatibilité : supprime la session."""
    clear_session(user_id)
