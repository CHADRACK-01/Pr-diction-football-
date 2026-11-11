# core/api/bzzoiro.py
"""
Client Bzzoiro.
- Normalisation compétition : code interne OU nom propre reconnu
- Retry sur 429/5xx
- Logs enrichis
"""

import time
import requests
from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error, log_warning
from config import BZZOIRO_API_KEY

BASE_URL = "https://sports.bzzoiro.com/api/v2"
TZ_KINSHASA = timezone(timedelta(hours=1))

MAX_RETRIES = 2
BACKOFF_SEC = 2
TIMEOUT = 15


def _get_headers():
    """Headers d'authentification Bzzoiro."""
    if not BZZOIRO_API_KEY:
        return {"Content-Type": "application/json"}
    return {
        "Authorization": f"Token {BZZOIRO_API_KEY}",
        "Content-Type": "application/json",
    }


def _extraire_message_erreur(res):
    """Extrait un message d'erreur lisible."""
    try:
        data = res.json()
        if isinstance(data, dict):
            return data.get("detail") or data.get("error") or str(data)[:200]
    except Exception:
        pass
    return res.text[:200] if res.text else ""


def _faire_requete(url, params, contexte_extra):
    """Requête avec retry. Retourne (res, tentative)."""
    headers = _get_headers()

    for tentative in range(1, MAX_RETRIES + 1):
        try:
            debut = time.time()
            res = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            duree_ms = int((time.time() - debut) * 1000)

            if res.status_code == 200:
                return res, tentative

            if res.status_code == 401:
                log_error(
                    message="Bzzoiro : clé API invalide (401)",
                    module="API",
                    api_context={
                        "source": "bzzoiro",
                        "url": url,
                        "http_status": 401,
                        "http_body": _extraire_message_erreur(res),
                    },
                    extra=contexte_extra,
                )
                return res, tentative

            if res.status_code == 429 or res.status_code >= 500:
                log_warning(
                    message=f"Bzzoiro HTTP {res.status_code} (tentative {tentative}/{MAX_RETRIES})",
                    module="API",
                    api_context={
                        "source": "bzzoiro",
                        "url": url,
                        "http_status": res.status_code,
                        "http_body": _extraire_message_erreur(res),
                        "attempt": f"{tentative}/{MAX_RETRIES}",
                        "duration_ms": duree_ms,
                    },
                    extra=contexte_extra,
                )
                if tentative < MAX_RETRIES:
                    time.sleep(BACKOFF_SEC * tentative)
                    continue
                return res, tentative

            # Autres codes
            log_warning(
                message=f"Bzzoiro HTTP inattendu {res.status_code}",
                module="API",
                api_context={
                    "source": "bzzoiro",
                    "url": url,
                    "http_status": res.status_code,
                    "http_body": _extraire_message_erreur(res),
                },
                extra=contexte_extra,
            )
            return res, tentative

        except requests.exceptions.Timeout as e:
            log_warning(
                message=f"Bzzoiro timeout (tentative {tentative}/{MAX_RETRIES})",
                module="API",
                api_context={
                    "source": "bzzoiro",
                    "url": url,
                    "attempt": f"{tentative}/{MAX_RETRIES}",
                },
                extra=contexte_extra,
                exception=e,
            )
            if tentative < MAX_RETRIES:
                time.sleep(BACKOFF_SEC * tentative)
                continue
            return None, tentative

        except requests.exceptions.ConnectionError as e:
            log_warning(
                message=f"Bzzoiro connexion impossible (tentative {tentative}/{MAX_RETRIES})",
                module="API",
                api_context={
                    "source": "bzzoiro",
                    "url": url,
                    "attempt": f"{tentative}/{MAX_RETRIES}",
                },
                extra=contexte_extra,
                exception=e,
            )
            if tentative < MAX_RETRIES:
                time.sleep(BACKOFF_SEC * tentative)
                continue
            return None, tentative

        except Exception as e:
            log_error(
                message="Bzzoiro erreur inattendue",
                module="API",
                api_context={"source": "bzzoiro", "url": url},
                extra=contexte_extra,
                exception=e,
            )
            return None, tentative

    return None, MAX_RETRIES


def tester_api():
    """Vérifie si Bzzoiro répond."""
    if not BZZOIRO_API_KEY:
        log_warning(
            message="Bzzoiro : clé API manquante",
            module="API",
            api_context={"source": "bzzoiro"},
        )
        return False

    res, _ = _faire_requete(
        f"{BASE_URL}/coverage/", None, {"operation": "tester_api"}
    )
    if res is None:
        return False
    if res.status_code == 200:
        log_info("Bzzoiro : OK", "API")
        return True
    return False


def get_matchs_du_jour():
    """
    Récupère les matchs à venir (2 jours) depuis Bzzoiro.
    Normalise `competition` en code interne (via mapping config).
    """
    from config import MAPPING_COMPETITIONS

    maintenant = datetime.now(TZ_KINSHASA)
    date_debut = int(maintenant.timestamp())
    date_fin = int((maintenant + timedelta(days=2)).timestamp())

    url = f"{BASE_URL}/events/"
    params = {
        "date_from": date_debut,
        "date_to": date_fin,
        "status": "scheduled",
    }

    res, tentative = _faire_requete(url, params, {"operation": "matchs_du_jour"})

    if res is None or res.status_code != 200:
        log_error(
            message="Bzzoiro : impossible de récupérer les matchs",
            module="API",
            api_context={
                "source": "bzzoiro",
                "url": url,
                "http_status": res.status_code if res else None,
            },
        )
        return []

    try:
        data = res.json()
    except Exception as e:
        log_error(
            message="Bzzoiro : parse JSON échoué",
            module="API",
            api_context={"source": "bzzoiro", "url": url},
            exception=e,
        )
        return []

    matchs_bruts = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(matchs_bruts, list):
        log_warning(
            message="Bzzoiro : format de réponse inattendu (pas une liste)",
            module="API",
            api_context={"source": "bzzoiro", "url": url},
            extra={"type_recu": type(matchs_bruts).__name__},
        )
        return []

    # Reverse mapping : nom propre -> code interne
    noms_vers_codes = {v: k for k, v in MAPPING_COMPETITIONS.items()}

    matchs_normalises = []
    erreurs_parsing = 0

    for m in matchs_bruts:
        if not isinstance(m, dict):
            erreurs_parsing += 1
            continue

        # Extraction équipes
        home = m.get("home_team")
        if isinstance(home, dict):
            home = home.get("name")
        away = m.get("away_team")
        if isinstance(away, dict):
            away = away.get("name")

        if not home or not away:
            erreurs_parsing += 1
            continue

        # Extraction compétition : nom -> code interne
        league = m.get("league")
        comp_name = None
        if isinstance(league, dict):
            comp_name = league.get("name")
        elif league:
            comp_name = str(league)

        # Normalisation : si le nom est connu, on convertit en code
        competition_finale = comp_name or "inconnu"
        if comp_name in noms_vers_codes:
            competition_finale = noms_vers_codes[comp_name]
        elif comp_name:
            # Tentative insensible à la casse
            comp_lower = comp_name.strip().lower()
            for nom, code in noms_vers_codes.items():
                if nom.strip().lower() == comp_lower:
                    competition_finale = code
                    break

        # Cotes
        odds = m.get("odds")
        cotes_book = None
        if isinstance(odds, dict):
            h, d, a = odds.get("home_win"), odds.get("draw"), odds.get("away_win")
            if h and d and a:
                cotes_book = {"h": h, "d": d, "a": a}

        # Heure
        heure = None
        for key in ("start_time", "start_date", "datetime", "date", "time", "utcDate"):
            if m.get(key):
                heure = m.get(key)
                break

        matchs_normalises.append({
            "competition": competition_finale,
            "heure": heure,
            "home": home,
            "away": away,
            "cotes_book": cotes_book,
        })

    if erreurs_parsing > 0:
        log_warning(
            message=f"Bzzoiro : {erreurs_parsing} matchs ignorés (données incomplètes)",
            module="API",
            api_context={"source": "bzzoiro", "url": url},
            extra={"erreurs_parsing": erreurs_parsing, "total": len(matchs_bruts)},
        )

    log_info(
        f"Bzzoiro : {len(matchs_normalises)} matchs normalisés",
        "API",
        extra={"total_brut": len(matchs_bruts)},
    )
    return matchs_normalises
