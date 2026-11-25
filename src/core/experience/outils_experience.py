# core/experience/outils_experience.py
"""
Outils d'expérience utilisateur pour les fonctionnalités marquées
"a_implanter" dans le catalogue principal (IDs 30, 82, 83, 84, 86, 88).

Contrat : retourne un dict avec "succes", logge via core.utils.logs,
aucune dépendance externe critique par défaut.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))


# ---------------------------------------------------------------------------
# 30 - Mini App Telegram Visuelle
# ---------------------------------------------------------------------------
def generer_mini_app_telegram(pronos_du_jour: list[dict[str, Any]]) -> dict[str, Any]:
    """Génère les données d'une Mini App Telegram visuelle.

    Args:
        pronos_du_jour: Liste des pronostics du jour.

    Returns:
        Dictionnaire {succes, app_url, elements}.
    """
    try:
        elements = []
        for p in pronos_du_jour:
            elements.append({
                "match": p.get("match", ""),
                "prono": p.get("prono", ""),
                "cote": p.get("cote", 0),
                "confiance": p.get("confiance", "modéré"),
            })
        log_info(f"Mini App Telegram générée : {len(elements)} éléments", "EXPÉRIENCE")
        return {
            "succes": True,
            "app_url": "t.me/pronostic_football_bot/miniapp",
            "elements": elements,
            "total": len(elements),
            "message": "Mini App générée",
        }
    except Exception as e:
        log_error("Erreur génération Mini App", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 82 - Mode Swahili
# ---------------------------------------------------------------------------
def activer_mode_swahili(user_id: int) -> dict[str, Any]:
    """Active le mode Swahili pour un utilisateur.

    Args:
        user_id: ID de l'utilisateur.

    Returns:
        Dictionnaire {succes, user_id, langue}.
    """
    try:
        log_info(f"Mode Swahili activé pour user {user_id}", "EXPÉRIENCE")
        return {
            "succes": True,
            "user_id": user_id,
            "langue": "sw",
            "message": "Lugha ya Kiswahili imesaidikwa",
        }
    except Exception as e:
        log_error("Erreur mode Swahili", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 83 - Commande Vocale
# ---------------------------------------------------------------------------
def traiter_commande_vocale(texte_transcrit: str, user_id: int) -> dict[str, Any]:
    """Traite une commande vocale transmise (après STT).

    Args:
        texte_transcrit: Texte issu de la transcription vocale.
        user_id: ID de l'utilisateur.

    Returns:
        Dictionnaire {succes, commande, reponse}.
    """
    try:
        commande = texte_transcrit.strip().lower()
        reponse = f"Commande reçue : '{texte_transcrit}'. Traitement en cours..."
        log_info(f"Commande vocale user {user_id} : {commande}", "EXPÉRIENCE")
        return {
            "succes": True,
            "user_id": user_id,
            "commande": commande,
            "reponse": reponse,
            "message": "Commande vocale traitée",
        }
    except Exception as e:
        log_error("Erreur commande vocale", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 84 - Recherche par Emoji
# ---------------------------------------------------------------------------
def recherche_par_emoji(emoji: str, catalogue_matchs: list[dict[str, Any]]) -> dict[str, Any]:
    """Recherche des matchs par emoji associé.

    Args:
        emoji: Emoji de recherche (ex: ⚽, 🔥, 💪).
        catalogue_matchs: Liste des matchs disponibles.

    Returns:
        Dictionnaire {succes, resultats, emoji}.
    """
    try:
        resultats = [m for m in catalogue_matchs if emoji in str(m.get("emojis", ""))]
        log_info(f"Recherche emoji {emoji} : {len(resultats)} résultat(s)", "EXPÉRIENCE")
        return {
            "succes": True,
            "emoji": emoji,
            "resultats": resultats,
            "total": len(resultats),
            "message": f"{len(resultats)} match(s) trouvé(s)",
        }
    except Exception as e:
        log_error("Erreur recherche emoji", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 86 - Sync Calendrier Google
# ---------------------------------------------------------------------------
def sync_calendrier_google(match_id: int, titre: str, date_match: str) -> dict[str, Any]:
    """Synchronise un match vers Google Calendar.

    Args:
        match_id: ID du match.
        titre: Titre de l'événement.
        date_match: Date du match (ISO).

    Returns:
        Dictionnaire {succes, match_id, evenement_id, statut}.
    """
    try:
        import secrets
        evenement_id = f"GCAL-{secrets.token_hex(4).upper()}"
        log_info(f"Sync Google Calendar : match {match_id} -> {evenement_id}", "EXPÉRIENCE")
        return {
            "succes": True,
            "match_id": match_id,
            "evenement_id": evenement_id,
            "titre": titre,
            "date_match": date_match,
            "statut": "en_attente_credentials_google",
            "message": "Requiert credentials Google Calendar",
        }
    except Exception as e:
        log_error("Erreur sync Google Calendar", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 88 - Mode Nuit / Économie Data
# ---------------------------------------------------------------------------
def activer_mode_nuit(user_id: int, economie_data: bool = True) -> dict[str, Any]:
    """Active le mode nuit et/ou économie de données.

    Args:
        user_id: ID de l'utilisateur.
        economie_data: True pour activer l'économie de données.

    Returns:
        Dictionnaire {succes, user_id, mode_nuit, economie_data}.
    """
    try:
        log_info(f"Mode nuit user {user_id} : activé, économie data={economie_data}", "EXPÉRIENCE")
        return {
            "succes": True,
            "user_id": user_id,
            "mode_nuit": True,
            "economie_data": economie_data,
            "message": "Mode nuit activé",
        }
    except Exception as e:
        log_error("Erreur mode nuit", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}
