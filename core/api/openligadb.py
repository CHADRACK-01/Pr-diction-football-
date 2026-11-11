# core/api/openligadb.py
"""
Client OpenLigaDB.
⚠️ CORRECTION MAJEURE : la journée courante est calculée dynamiquement
au lieu d'être hardcodée à /1.
"""

import requests
from datetime import datetime, timezone, timedelta

from core.utils.logs import log_info, log_error, log_warning

BASE_URL = "https://api.openligadb.de"
TZ_KINSHASA = timezone(timedelta(hours=1))
TIMEOUT = 15

LIGUES_OPENLIGADB = {
    "bl1": "bundesliga_1",
    "bl2": "bundesliga_2",
}


def tester_api():
    """Vérifie si OpenLigaDB répond."""
    try:
        res = requests.get(f"{BASE_URL}/getavailableleagues", timeout=TIMEOUT)
        if res.status_code == 200:
            log_info("OpenLigaDB : OK", "API")
            return True
        log_warning(
            message=f"OpenLigaDB : statut {res.status_code}",
            module="API",
            api_context={"source": "openligadb", "http_status": res.status_code},
        )
        return False
    except Exception as e:
        log_error(
            message="OpenLigaDB : impossible de se connecter",
            module="API",
            api_context={"source": "openligadb", "url": f"{BASE_URL}/getavailableleagues"},
            exception=e,
        )
        return False


def _saison_courante():
    """Retourne l'année de début de saison (juillet = nouvelle saison)."""
    now = datetime.now(TZ_KINSHASA)
    return now.year if now.month >= 7 else now.year - 1


def _recuperer_journee_courante(shortcut, saison):
    """
    Récupère la journée courante via l'endpoint sans numéro de journée,
    puis détermine le numéro de la journée en cours.
    Fallback : journée 1 si échec.
    """
    url = f"{BASE_URL}/getmatchdata/{shortcut}/{saison}"
    try:
        res = requests.get(url, timeout=TIMEOUT)
        if res.status_code != 200:
            log_warning(
                message=f"OpenLigaDB : impossible de récupérer le calendrier {shortcut}/{saison}",
                module="API",
                api_context={
                    "source": "openligadb",
                    "url": url,
                    "http_status": res.status_code,
                },
            )
            return 1  # fallback

        data = res.json()
        if not isinstance(data, list) or not data:
            return 1

        maintenant = datetime.now(TZ_KINSHASA)
        journee_courante = None

        for m in data:
            if not isinstance(m, dict):
                continue
            group = m.get("group") or {}
            journee = group.get("groupOrderID")
            dt_str = m.get("matchDateTimeUTC")
            if not journee or not dt_str:
                continue
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                # La journée qui contient le match le plus proche du présent
                if dt >= maintenant:
                    if journee_courante is None or journee < journee_courante:
                        journee_courante = journee
            except Exception:
                continue

        if journee_courante is None:
            # Aucun match futur : on prend la dernière journée
            journees = []
            for m in data:
                if not isinstance(m, dict):
                    continue
                group = m.get("group") or {}
                j = group.get("groupOrderID")
                if j:
                    journees.append(j)
            journee_courante = max(journees) if journees else 1

        log_info(
            f"OpenLigaDB {shortcut}/{saison} : journée courante = {journee_courante}",
            "API",
        )
        return journee_courante

    except Exception as e:
        log_error(
            message=f"OpenLigaDB : erreur calcul journée courante {shortcut}",
            module="API",
            api_context={"source": "openligadb", "url": url},
            exception=e,
        )
        return 1


def get_matchs_du_jour():
    """
    Récupère les matchs à venir pour la journée courante de chaque ligue.
    Normalise competition en code interne.
    """
    matchs_normalises = []
    ligues_reussies = 0
    ligues_echouees = 0
    saison = _saison_courante()
    maintenant = datetime.now(TZ_KINSHASA)

    for shortcut, comp_code in LIGUES_OPENLIGADB.items():
        try:
            journee = _recuperer_journee_courante(shortcut, saison)
            url = f"{BASE_URL}/getmatchdata/{shortcut}/{saison}/{journee}"

            res = requests.get(url, timeout=TIMEOUT)

            if res.status_code == 404:
                log_warning(
                    message=f"OpenLigaDB : pas de données pour {shortcut} journée {journee} (404)",
                    module="API",
                    api_context={
                        "source": "openligadb",
                        "url": url,
                        "http_status": 404,
                    },
                )
                continue
            if res.status_code != 200:
                log_error(
                    message=f"OpenLigaDB : erreur {res.status_code} pour {shortcut}",
                    module="API",
                    api_context={
                        "source": "openligadb",
                        "url": url,
                        "http_status": res.status_code,
                    },
                )
                ligues_echouees += 1
                continue

            data = res.json()
            if not isinstance(data, list):
                log_warning(
                    message=f"OpenLigaDB : format inattendu pour {shortcut}",
                    module="API",
                    api_context={"source": "openligadb", "url": url},
                )
                continue

            count_ligue = 0
            for m in data:
                if not isinstance(m, dict):
                    continue
                if m.get("matchIsFinished"):
                    continue

                team1 = m.get("team1") or {}
                team2 = m.get("team2") or {}
                home = team1.get("teamName")
                away = team2.get("teamName")
                heure = m.get("matchDateTimeUTC")

                if not home or not away or not heure:
                    continue

                # ⚠️ Vérification : on garde uniquement les matchs futurs ou du jour
                try:
                    dt = datetime.fromisoformat(heure.replace("Z", "+00:00"))
                    if dt < maintenant - timedelta(hours=6):
                        # Match trop ancien (déjà terminé ou en cours depuis longtemps)
                        continue
                except Exception:
                    continue

                matchs_normalises.append({
                    "competition": comp_code,
                    "heure": heure,
                    "home": home,
                    "away": away,
                    "cotes_book": None,
                    "logo_home": team1.get("teamIconUrl"),
                    "logo_away": team2.get("teamIconUrl"),
                })
                count_ligue += 1

            ligues_reussies += 1
            log_info(
                f"OpenLigaDB / {shortcut} journée {journee} : {count_ligue} matchs",
                "API",
                extra={"competition": comp_code, "journee": journee},
            )

        except requests.exceptions.Timeout as e:
            ligues_echouees += 1
            log_warning(
                message=f"OpenLigaDB : timeout pour {shortcut}",
                module="API",
                api_context={"source": "openligadb", "competition": shortcut},
                exception=e,
            )
        except Exception as e:
            ligues_echouees += 1
            log_error(
                message=f"OpenLigaDB : erreur inattendue pour {shortcut}",
                module="API",
                api_context={"source": "openligadb", "competition": shortcut},
                exception=e,
            )

    if ligues_reussies == 0 and ligues_echouees > 0:
        log_error(
            message=f"OpenLigaDB : aucune ligue n'a répondu ({ligues_echouees} échecs)",
            module="API",
            api_context={"source": "openligadb"},
            extra={"echecs": ligues_echouees},
        )
    else:
        log_info(
            f"OpenLigaDB : {len(matchs_normalises)} matchs au total "
            f"({ligues_reussies} OK, {ligues_echouees} échecs)",
            "API",
        )

    return matchs_normalises
