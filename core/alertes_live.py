# core/alertes_live.py
"""
Alertes de buts en direct.

Interroge l'API-Football (``/fixtures?live=all``), compare les scores des matchs
en cours avec ceux mémorisés dans ``_SCORES_PRECEDENTS`` et envoie un message
« ⚽ BUT ! ... » aux utilisateurs notifiés à chaque changement de score.

⚠️ ``verifier_buts_live`` n'est appelée nulle part pour le moment : un créneau
live dans le scheduler (app.py) sera ajouté dans une PR suivante.
"""

from core.api.api_football import _faire_requete, BASE_URL
from users import get_utilisateurs_notifies
from core.utils.logs import log_info, log_warning

# fixture_id -> (score_home, score_away)
_SCORES_PRECEDENTS = {}


def verifier_buts_live(bot):
    """
    Vérifie les matchs en direct et alerte les utilisateurs notifiés à chaque but.

    Retourne le nombre d'alertes envoyées.
    """
    url = f"{BASE_URL}/fixtures?live=all"
    res, _ = _faire_requete(url, {"source": "alertes_live"})

    if not res or res.status_code != 200:
        log_warning(
            message="Alertes live : fixtures en direct indisponibles",
            module="ALERTES",
            api_context={
                "source": "alertes_live",
                "url": url,
                "http_status": res.status_code if res else None,
            },
        )
        return 0

    try:
        data = res.json()
    except Exception as e:
        log_warning(
            message="Alertes live : parse de la réponse échoué",
            module="ALERTES",
            api_context={"source": "alertes_live", "url": url},
            exception=e,
        )
        return 0

    fixtures = data.get("response", [])
    scores_actuels = {}
    alertes = 0

    for match in fixtures:
        try:
            fixture_id = match.get("fixture", {}).get("id")
            if fixture_id is None:
                continue

            buts = match.get("goals", {})
            score_home = buts.get("home")
            score_away = buts.get("away")
            if score_home is None or score_away is None:
                continue

            home = match.get("teams", {}).get("home", {}).get("name", "?")
            away = match.get("teams", {}).get("away", {}).get("name", "?")
            minute = match.get("fixture", {}).get("status", {}).get("elapsed") or 0

            scores_actuels[fixture_id] = (score_home, score_away)

            # Amorçage : match inconnu (1er cycle ou redémarrage), on mémorise sans alerter
            if fixture_id not in _SCORES_PRECEDENTS:
                continue

            if _SCORES_PRECEDENTS[fixture_id] != (score_home, score_away):
                texte = (
                    f"⚽ BUT ! {home} {score_home} - {score_away} {away} "
                    f"(minute {minute})"
                )
                for user_id in get_utilisateurs_notifies():
                    try:
                        bot.send_message(user_id, texte)
                    except Exception as e:
                        log_warning(
                            message=f"Alertes live : envoi échoué à {user_id}",
                            module="ALERTES",
                            user_context={"user_id": user_id},
                            exception=e,
                        )
                alertes += 1
        except Exception as e:
            log_warning(
                message="Alertes live : match ignoré (données invalides)",
                module="ALERTES",
                exception=e,
            )
            continue

    # Mise à jour complète : les fixture_id absents de la réponse live sont purgés
    _SCORES_PRECEDENTS.clear()
    _SCORES_PRECEDENTS.update(scores_actuels)

    log_info(
        f"Alertes live : {len(scores_actuels)} match(s) suivi(s), "
        f"{alertes} alerte(s) envoyée(s)",
        "ALERTES",
    )
    return alertes
