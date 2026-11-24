# app.py
"""
Point d'entrée Flask + Scheduler.
- Routes debug protégées par secret
- Lock sur l'initialisation DB
- Scheduler avec persistance des dernières exécutions (table parametres)
- Health en try/finally
- verifier_configuration() bloquante au démarrage
- Formatage HTML pour Telegram
"""

import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import time
import threading
import telebot
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, request

# =========================================================
# CAPTURE GLOBALE
# =========================================================
from core.utils.error_handler import activer_capture_globale
activer_capture_globale()

# =========================================================
# CONFIG (bloquante si critique manquante)
# =========================================================
from config import (
    TOKEN, MODE_VITRINE, TURSO_URL, TURSO_TOKEN,
    ADMIN_ID, verifier_configuration, MODE_TEST
)
verifier_configuration()

from users import (
    get_utilisateurs_notifies, est_banni,
    est_administrateur, get_parametre, set_parametre,
)
from telegram_bot.handlers import enregistrer_handlers
from core.utils.logs import log_info, log_error, log_warning, log_critical

# Initialisation bot + Flask
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Handlers
try:
    enregistrer_handlers(bot)
except Exception as e:
    log_critical(
        message="Impossible d'enregistrer les handlers Telegram",
        module="BOOT",
        exception=e,
    )
    raise

TZ_KINSHASA = timezone(timedelta(hours=1))

# =========================================================
# LOCK DB (thread-safe)
# =========================================================
_db_lock = threading.Lock()
_db_initialisee = False


def _initialiser_bdd_si_necessaire():
    global _db_initialisee
    if _db_initialisee:
        return
    with _db_lock:
        if _db_initialisee:
            return
        try:
            from users.db import initialiser_tables
            log_info("Initialisation BDD (lazy)...", "BOOT")
            initialiser_tables()
            _db_initialisee = True
            log_info("BDD initialisée.", "BOOT")
        except Exception as e:
            log_critical(
                message="Impossible d'initialiser la BDD",
                module="BOOT",
                exception=e,
            )
            raise

# =========================================================
# MIDDLEWARE FLASK
# =========================================================
@app.errorhandler(Exception)
def gerer_erreur_globale(e):
    log_error(
        message=f"Erreur Flask non gérée : {e}",
        module="FLASK",
        extra={"route": request.path, "method": request.method},
        exception=e,
    )
    return "❌ Erreur interne.", 500

# =========================================================
# UTILITAIRES
# =========================================================
def _envoyer_message_securise(chat_id, texte, parse_mode="HTML"):
    if MODE_TEST:
        log_info("Mode Test : envoi de message ignoré.", "NOTIFS")
        return True

    limite = 4000
    if len(texte) <= limite:
        try:
            bot.send_message(chat_id, texte, parse_mode=parse_mode)
            return True
        except Exception:
            try:
                bot.send_message(chat_id, texte)
                return True
            except Exception:
                return False

    morceaux = [texte[i:i + limite] for i in range(0, len(texte), limite)]
    for morceau in morceaux:
        try:
            bot.send_message(chat_id, morceau, parse_mode=parse_mode)
        except Exception:
            try: bot.send_message(chat_id, morceau)
            except Exception: return False
        time.sleep(0.3)
    return True


def charger_modele_universel():
    from core.ml_model import global_model_data, charger_et_entrainer
    if global_model_data.get("models") is not None:
        return True
    if charger_et_entrainer():
        log_info("Modèles chargés.", "BOOT")
        return True
    log_warning("Impossible de charger les modèles.", "BOOT")
    return False

# =========================================================
# PERSISTANCE DES DERNIÈRES EXÉCUTIONS
# =========================================================
def _get_derniere_execution(cle, defaut=None):
    try:
        return get_parametre(f"sched_{cle}", defaut)
    except Exception:
        return defaut


def _set_derniere_execution(cle, date_str):
    try:
        set_parametre(f"sched_{cle}", date_str, f"Dernière exécution {cle}")
    except Exception as e:
        log_error(f"Impossible de persister la dernière exécution '{cle}'", "SCHEDULER", exception=e)


# Import en tête de module (et non local au scheduler) pour que toute
# ImportError sur expirer_premiums soit visible et ne soit plus masquée
# par le try/except du bloc 03:15.
from users import expirer_premiums

# =========================================================
# TÂCHES AUTOMATIQUES
# =========================================================
def _mettre_a_jour_resultats():
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats
        total = mettre_a_jour_resultats()
        log_info(f"Résultats mis à jour : {total} matchs.", "SCHEDULER")
    except Exception as e:
        log_error(message="Erreur maj résultats", module="SCHEDULER", exception=e)


def _telecharger_nouveaux_matchs():
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        log_info(f"Matchs téléchargés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error(message="Erreur téléchargement matchs", module="SCHEDULER", exception=e)


def _nettoyer_vieilles_donnees():
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        log_info(f"Matchs de plus de 5 ans supprimés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error(message="Erreur nettoyage vieilles données", module="SCHEDULER", exception=e)


def _envoyer_notifications():
    if MODE_TEST:
        log_info("Mode Test : envoi de notifications ignoré.", "NOTIFS")
        return

    if not charger_modele_universel():
        return

    try:
        from core.daily_matches import get_matchs_du_jour
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error(message="Erreur récupération matchs notifs", module="NOTIFS", exception=e)
        return

    if not matchs:
        log_warning("Aucun match pour les notifications du matin.", "NOTIFS")
        return

    top_3 = sorted(matchs, key=lambda x: x.get("dc_pct", 0), reverse=True)[:3]
    
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    texte = f"👋 <b>BONJOUR ! VOICI MES 3 CONSEILS DU JOUR</b>\nDate : {date_str}\n\n"
    
    for i, m in enumerate(top_3, 1):
        label = m.get("dc_label", "1X")
        if label == "1X":
            conseil = f"<b>{m['home']}</b> gagne ou fait match nul"
        elif label == "X2":
            conseil = f"<b>{m['away']}</b> gagne ou fait match nul"
        else:
            conseil = "Il n'y aura pas de match nul"

        texte += f"{i}. <b>{m['home']} vs {m['away']}</b>\n"
        texte += f"   👉 Mon conseil : {conseil}\n"
        texte += f"   📊 (Fiabilité : {round(m.get('dc_pct', 0) * 100, 1)}%)\n\n"

    texte += "━━━━━━━━━━━━━━━━━━━━\n"
    texte += "💡 <i>Misez max 2% de votre capital par pari.</i>"

    users = get_utilisateurs_notifies()
    succes = 0
    for uid in users:
        if _envoyer_message_securise(uid, texte, parse_mode="HTML"):
            succes += 1
        time.sleep(0.1)
        
    log_info(f"Notifications du matin envoyées : {succes}", "NOTIFS")


def _envoyer_coupons_premium():
    if MODE_TEST:
        log_info("Mode Test : envoi de coupons ignoré.", "COUPONS")
        return
    if not charger_modele_universel():
        return
    try:
        from core.paris_builder import generer_coupons_du_jour, formater_coupon
        from users import get_langue
        from users.account_base import _parser_date
        from users.db import db_fetchall
        data = generer_coupons_du_jour()
        coupons = data["coupons"]
        if not coupons:
            return
        maintenant = datetime.now()
        rows = db_fetchall(
            "SELECT user_id, date_expiration FROM utilisateurs "
            "WHERE status = 'premium' "
            "AND date_expiration IS NOT NULL "
            "AND user_id NOT IN (SELECT user_id FROM bannis)"
        )
        premiums = []
        if rows:
            for r in rows:
                expiration_dt = _parser_date(r[1] if len(r) > 1 else None)
                if expiration_dt is not None and expiration_dt > maintenant:
                    premiums.append(r[0])
        for uid in premiums:
            langue = get_langue(uid)
            for coupon in coupons:
                texte = formater_coupon(coupon, langue, montrer_details=True)
                _envoyer_message_securise(uid, texte, parse_mode="HTML")
                time.sleep(0.1)
    except Exception as e:
        log_error(message="Erreur envoi coupons", module="COUPONS", exception=e)

# =========================================================
# SCHEDULER
# =========================================================
def _scheduler_notifications():
    global _derniere_alerte_live, _derniere_verif_apis, _derniere_verif_quota, _derniere_verif_pic
    log_info("Scheduler démarré...", "SCHEDULER")
    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5
            date_du_jour = now.strftime("%Y-%m-%d")

            try:
                heure_notif = int(get_parametre("notif_heure", "8"))
            except Exception:
                heure_notif = 8

            _initialiser_bdd_si_necessaire()

            # 02:00 — Mise à jour des résultats (à partir de 02:00, une seule fois par jour)
            if now.hour == 2:
                if _get_derniere_execution("maj_resultats") != date_du_jour:
                    log_info("Mise à jour des résultats...", "SCHEDULER")
                    _mettre_a_jour_resultats()
                    _set_derniere_execution("maj_resultats", date_du_jour)

            # 03:00 — Téléchargement matchs (à partir de 03:00, une seule fois par jour)
            if now.hour == 3:
                if _get_derniere_execution("telechargement") != date_du_jour:
                    log_info("Téléchargement des matchs...", "SCHEDULER")
                    _telecharger_nouveaux_matchs()
                    _set_derniere_execution("telechargement", date_du_jour)

            # 03:05 — Nettoyage vieilles données
            if now.hour == 3 and now.minute >= 5:
                if _get_derniere_execution("nettoyage_donnees") != date_du_jour:
                    _nettoyer_vieilles_donnees()
                    _set_derniere_execution("nettoyage_donnees", date_du_jour)

            # 03:15 — Expiration des abonnements premium
            if now.hour == 3 and now.minute >= 15:
                if _get_derniere_execution("expiration_premium") != date_du_jour:
                    try:
                        nb_bascules = expirer_premiums()
                        _set_derniere_execution("expiration_premium", date_du_jour)
                        log_info(
                            f"Expiration premium : {nb_bascules} compte(s) basculé(s) en free",
                            "SCHEDULER",
                        )
                    except ImportError as e:
                        log_warning(
                            message="Import de expirer_premiums impossible",
                            module="SCHEDULER",
                            exception=e,
                        )
                    except Exception as e:
                        log_error(
                            message="Erreur expiration premium",
                            module="SCHEDULER",
                            exception=e,
                        )

            # heure_notif — Envoi notifications + canal
            if now.hour == heure_notif:
                if _get_derniere_execution("notifs_jour") != date_du_jour:
                    _envoyer_notifications()
                    _set_derniere_execution("notifs_jour", date_du_jour)
                    if est_weekend:
                        _envoyer_coupons_premium()

            # Alertes live (buts en direct) : une vérification par tranche de 5 min.
            # Le créneau est mémorisé, donc même si la boucle décale d'une minute,
            # la tranche n'est jamais manquée ni traitée deux fois.
            creneau = f"{date_du_jour}-{now.hour:02d}-{now.minute // 5}"
            if creneau != _derniere_alerte_live:
                _derniere_alerte_live = creneau
                try:
                    alertes = verifier_buts_live(bot)
                    if alertes > 0:
                        log_info(f"Alertes live : {alertes} alerte(s) envoyée(s)", "SCHEDULER")
                except Exception as e:
                    log_error(message="Erreur alertes live", module="SCHEDULER", exception=e)

            # Santé des APIs de données (fonctionnalité 133) : contrôle toutes les 15 min.
            # Alerte admin après 2 échecs consécutifs, puis rétablissement signalé.
            creneau_api = f"api-{date_du_jour}-{now.hour:02d}-{now.minute // 15}"
            if creneau_api != _derniere_verif_apis:
                _derniere_verif_apis = creneau_api
                try:
                    from core.alerte_apis import verifier_et_alerter

                    def _alerter_admin(texte):
                        if ADMIN_ID is not None:
                            bot.send_message(ADMIN_ID, "⚠️ <b>Santé des APIs</b>\n" + texte, parse_mode="HTML")

                    verifier_et_alerter(_alerter_admin)
                except Exception as e:
                    log_error(message="Erreur contrôle APIs", module="SCHEDULER", exception=e)

            # Consommation des API (fonctionnalité 135) : contrôle une fois par heure.
            creneau_quota = f"quota-{date_du_jour}-{now.hour:02d}"
            if creneau_quota != _derniere_verif_quota:
                _derniere_verif_quota = creneau_quota
                try:
                    from core.controle_quota import controler_et_alerter

                    def _alerter_quota(texte):
                        if ADMIN_ID is not None:
                            bot.send_message(ADMIN_ID, "📊 <b>Quota API</b>\n" + texte, parse_mode="HTML")

                    controler_et_alerter(_alerter_quota)
                except Exception as e:
                    log_error(message="Erreur contrôle quota", module="SCHEDULER", exception=e)

            # Pic d'erreurs (fonctionnalité 134) : contrôle toutes les 5 min.
            creneau_pic = f"pic-{date_du_jour}-{now.hour:02d}-{now.minute // 5}"
            if creneau_pic != _derniere_verif_pic:
                _derniere_verif_pic = creneau_pic
                try:
                    from core.pic_erreurs import controler_et_alerter as _controler_pic

                    def _alerter_pic(texte):
                        if ADMIN_ID is not None:
                            bot.send_message(ADMIN_ID, texte)

                    _controler_pic(_alerter_pic)
                except Exception as e:
                    log_error(message="Erreur contrôle pic d'erreurs", module="SCHEDULER", exception=e)

            time.sleep(60)
        except Exception as e:
            log_error(message="Erreur critique scheduler", module="SCHEDULER", exception=e)
            time.sleep(60)


from core.alertes_live import verifier_buts_live

_derniere_alerte_live = None
_derniere_verif_apis = None
_derniere_verif_quota = None
_derniere_verif_pic = None


def _lancer_scheduler_apres_delai():
    time.sleep(60)
    try:
        _scheduler_notifications()
    except Exception as e:
        log_critical(message="Le scheduler s'est arrêté", module="SCHEDULER", exception=e)

# =========================================================
# DÉMARRAGE ORIENTÉ OBJET
# =========================================================
from types import SimpleNamespace
from web.application import ApplicationRuntime

_runtime_config = SimpleNamespace(
    TURSO_URL=TURSO_URL,
    TURSO_TOKEN=TURSO_TOKEN,
    TOKEN=TOKEN,
    MODE_VITRINE=MODE_VITRINE,
    MODE_TEST=MODE_TEST,
    ADMIN_ID=ADMIN_ID,
)

runtime = ApplicationRuntime(
    app=app,
    bot=bot,
    config=_runtime_config,
    initialiser_bdd=_initialiser_bdd_si_necessaire,
    scheduler_callback=_scheduler_notifications,
)
runtime.start()
