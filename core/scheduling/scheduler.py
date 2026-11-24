"""Boucle planifiée, indépendante des routes Flask."""

import time
from datetime import datetime

from core.utils.logs import log_error, log_info


class SchedulerState:
    def __init__(self):
        self.alertes_live = None
        self.sante_apis = None
        self.quota_apis = None
        self.pic_erreurs = None


def cle_intervalle(now, date_du_jour, minutes):
    return f"{date_du_jour}-{now.hour:02d}-{now.minute // minutes}"


def lancer_scheduler(*, bot, timezone, initialiser_bdd, get_parametre,
                     obtenir_derniere_execution, persister_derniere_execution,
                     expirer_premiums, alerter_admin=None, controler_quota=None,
                     controler_pic=None, mode_test=False, sleep_seconds=60):
    """Boucle principale avec services injectés pour faciliter les tests."""
    state = SchedulerState()

    if mode_test:
        log_info("Mode Test : scheduler désactivé.", "SCHEDULER")
        return

    log_info("Scheduler démarré...", "SCHEDULER")
    while True:
        try:
            now = datetime.now(timezone)
            date_du_jour = now.strftime("%Y-%m-%d")

            try:
                heure_notif = int(get_parametre("notif_heure", "8"))
            except (TypeError, ValueError):
                heure_notif = 8

            initialiser_bdd()

            if now.hour == 2:
                if obtenir_derniere_execution("maj_resultats") != date_du_jour:
                    from core.scheduling.jobs import mettre_a_jour_resultats
                    mettre_a_jour_resultats()
                    persister_derniere_execution("maj_resultats", date_du_jour)

            if now.hour == 3:
                if obtenir_derniere_execution("telechargement") != date_du_jour:
                    from core.scheduling.jobs import telecharger_matchs
                    telecharger_matchs()
                    persister_derniere_execution("telechargement", date_du_jour)

                if now.minute >= 5 and obtenir_derniere_execution("nettoyage_donnees") != date_du_jour:
                    from core.scheduling.jobs import nettoyer_matchs_anciens
                    nettoyer_matchs_anciens()
                    persister_derniere_execution("nettoyage_donnees", date_du_jour)

                if now.minute >= 15 and obtenir_derniere_execution("expiration_premium") != date_du_jour:
                    try:
                        nombre = expirer_premiums()
                        persister_derniere_execution("expiration_premium", date_du_jour)
                        log_info(f"Expiration premium : {nombre} compte(s) basculé(s)", "SCHEDULER")
                    except Exception as e:
                        log_error("Erreur expiration premium", "SCHEDULER", exception=e)

            cle_live = cle_intervalle(now, date_du_jour, 5)
            if state.alertes_live != cle_live:
                state.alertes_live = cle_live
                try:
                    from core.alertes_live import verifier_buts_live
                    verifier_buts_live(bot)
                except Exception as e:
                    log_error("Erreur alertes live", "SCHEDULER", exception=e)

            cle_api = f"api-{date_du_jour}-{now.hour:02d}-{now.minute // 15}"
            if state.sante_apis != cle_api:
                state.sante_apis = cle_api
                try:
                    from core.alerte_apis import verifier_et_alerter
                    verifier_et_alerter(alerter_admin or (lambda texte: None))
                except Exception as e:
                    log_error("Erreur contrôle APIs", "SCHEDULER", exception=e)

            cle_quota = f"quota-{date_du_jour}-{now.hour:02d}"
            if state.quota_apis != cle_quota:
                state.quota_apis = cle_quota
                try:
                    if controler_quota:
                        controler_quota()
                except Exception as e:
                    log_error("Erreur contrôle quota", "SCHEDULER", exception=e)

            cle_pic = f"pic-{date_du_jour}-{now.hour:02d}-{now.minute // 5}"
            if state.pic_erreurs != cle_pic:
                state.pic_erreurs = cle_pic
                try:
                    if controler_pic:
                        controler_pic()
                except Exception as e:
                    log_error("Erreur contrôle pic d’erreurs", "SCHEDULER", exception=e)

            time.sleep(sleep_seconds)
        except Exception as e:
            log_error("Erreur critique scheduler", "SCHEDULER", exception=e)
            time.sleep(sleep_seconds)
