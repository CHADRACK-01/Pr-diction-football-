# core/administration/alertes_live.py
"""
Alertes live : buts en direct et suivi des paris (fonctionnalité 1).

Vérifie les scores en direct via un fournisseur de données sportives et
alerte les utilisateurs quand un but tombe, en indiquant si leur pari
est validé ou invalidé.

Dépendance externe : FournisseurDonneesSportives (api_football par défaut).
"""

from __future__ import annotations

from typing import Any

from core.adaptateurs.base import FournisseurDonneesSportives
from core.adaptateurs.factory import creer_adaptateur_sportif
from core.utils.logs import log_info, log_error


def verifier_buts_live(
    bot: Any,
    fournisseur: FournisseurDonneesSportives | None = None,
) -> int:
    """Vérifie les buts en direct et envoie des alertes aux utilisateurs.

    Pour chaque match en direct, compare le score actuel avec le score
    précédent. Si un but est détecté, notifie les utilisateurs concernés.

    Args:
        bot: Instance du bot Telegram (pyTelegramBotAPI TeleBot).
        fournisseur: Fournisseur de données sportives. Si None, utilise
                     l'adaptateur API-Football par défaut.

    Returns:
        Nombre d'alertes envoyées.
    """
    if fournisseur is None:
        fournisseur = creer_adaptateur_sportif()

    try:
        resultat = fournisseur.get_matchs_live()
        if not resultat.succes:
            log_error(
                f"Impossible de récupérer les matchs live : {resultat.erreur}",
                "ALERTES_LIVE",
            )
            return 0

        matchs_live = resultat.donnees or []
        alertes_envoyees = 0

        for match in matchs_live:
            try:
                # Structure attendue : dépend du fournisseur API-Football
                fixture = match.get("fixture", {})
                teams = match.get("teams", {})
                goals = match.get("goals", {})

                match_id = fixture.get("id")
                status = fixture.get("status", {}).get("short", "")
                if status != "LIVE":
                    continue

                home = teams.get("home", {}).get("name", "?")
                away = teams.get("away", {}).get("name", "?")
                score_h = goals.get("home", 0)
                score_a = goals.get("away", 0)

                # TODO : comparer avec le score précédent stocké en base
                # et notifier uniquement les utilisateurs ayant parié sur ce match

                log_info(
                    f"Match live : {home} {score_h} - {score_a} {away}",
                    "ALERTES_LIVE",
                    extra={"match_id": match_id, "score": f"{score_h}-{score_a}"},
                )

            except Exception as e:
                log_error(
                    "Erreur traitement match live",
                    "ALERTES_LIVE",
                    exception=e,
                )

        return alertes_envoyees

    except Exception as e:
        log_error(
            "Erreur lors de la vérification des buts live",
            "ALERTES_LIVE",
            exception=e,
        )
        return 0


def formater_alerte_but(
    match_home: str,
    match_away: str,
    score_home: int,
    score_away: int,
    buteur: str | None = None,
    minute: int | None = None,
) -> str:
    """Formate un message d'alerte but pour Telegram.

    Args:
        match_home: Nom de l'équipe à domicile.
        match_away: Nom de l'équipe à l'extérieur.
        score_home: Score domicile.
        score_away: Score extérieur.
        buteur: Nom du buteur (optionnel).
        minute: Minute du but (optionnel).

    Returns:
        Message formaté en HTML.
    """
    minute_str = f" ({minute}')" if minute else ""
    buteur_str = f" - {buteur}" if buteur else ""

    return (
        f"⚽ <b>BUT !</b>\n"
        f"{match_home} {score_home} - {score_away} {match_away}\n"
        f"🎯 {buteur or 'Buteur inconnu'}{minute_str}\n\n"
        f"📱 Consultez votre pari pour vérifier s'il est validé."
    )
