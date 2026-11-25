# core/controle_quota.py
"""
Contrôle de la consommation des API (fonctionnalité 135).

- Lit la consommation journalière de chaque clé API-Football
- Alerte l'admin quand une clé atteint SEUIL_ALERTE de son quota
- Une seule alerte par clé et par jour (état stocké dans la table parametres)

Lecture seule côté API : on interroge /status, qui ne consomme pas de quota métier.
"""

from datetime import datetime, timedelta, timezone

from core.utils.logs import log_info, log_error

SEUIL_ALERTE = 0.8
TZ_KINSHASA = timezone(timedelta(hours=1))
_PREFIXE_CLE = "quota_alerte_"


def evaluer(consommations, seuil=SEUIL_ALERTE):
    """Retourne les clés dont le quota est atteint, sous forme de dicts enrichis.

    Fonction pure : ne touche ni à la base ni au réseau.
    """
    depassements = []
    for c in consommations:
        limit = c.get("limit", 0)
        used = c.get("used", 0)
        if limit <= 0:
            continue
        taux = used / limit
        if taux >= seuil:
            depassements.append({"cle": c["cle"], "used": used, "limit": limit, "taux": taux})
    return depassements


def _aujourdhui():
    return datetime.now(TZ_KINSHASA).strftime("%Y-%m-%d")


def _deja_alerte_aujourdhui(cle):
    from users.admin import get_parametre
    return get_parametre(f"{_PREFIXE_CLE}{cle}", None) == _aujourdhui()


def _marquer_alerte(cle):
    from users.admin import set_parametre
    set_parametre(f"{_PREFIXE_CLE}{cle}", _aujourdhui(), f"Alerte quota clé {cle}")


def _lecteur_par_defaut():
    from core.api import api_football
    return api_football.lire_consommation()


def controler_et_alerter(envoyer, lecteur=None, deja_alerte=None, marquer=None, seuil=SEUIL_ALERTE):
    """Contrôle les quotas et envoie une alerte pour chaque clé dépassée (une fois par jour).

    Les paramètres deja_alerte et marquer permettent de remplacer le stockage
    (tests). Retourne le nombre d'alertes envoyées. Ne lève jamais d'exception.
    """
    try:
        consommations = (lecteur or _lecteur_par_defaut)()
        depassements = evaluer(consommations, seuil)
    except Exception as e:
        log_error(message="Contrôle des quotas impossible", module="API", exception=e)
        return 0

    deja = deja_alerte or _deja_alerte_aujourdhui
    marque = marquer or _marquer_alerte

    envoyees = 0
    for d in depassements:
        try:
            if deja(d["cle"]):
                continue
            envoyer(
                f"📊 Clé API-Football {d['cle']} : {d['used']}/{d['limit']} requêtes "
                f"aujourd'hui ({d['taux'] * 100:.0f} %)."
            )
            marque(d["cle"])
            envoyees += 1
        except Exception as e:
            log_error(message="Envoi de l'alerte quota impossible", module="API", exception=e)
    if envoyees:
        log_info(f"Alertes quota envoyées : {envoyees}", "API")
    return envoyees
