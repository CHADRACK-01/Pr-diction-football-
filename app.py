# app.py
"""
Point d'entrée Flask + Scheduler.
- Routes debug protégées par secret
- Lock sur l'initialisation DB
- Scheduler avec persistance des dernières exécutions (table parametres)
- Health en try/finally
- verifier_configuration() bloquante au démarrage
"""

import os
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import time
import threading
import telebot
import requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request

# =========================================================
# CAPTURE GLOBALE (avant tout import métier)
# =========================================================
from core.utils.error_handler import activer_capture_globale
activer_capture_globale()

# =========================================================
# CONFIG (bloquante si critique manquante)
# =========================================================
from config import (
    TOKEN, MODE_VITRINE, TURSO_URL, TURSO_TOKEN,
    ADMIN_ID, verifier_configuration,
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
    """Crée les tables Turso une seule fois (thread-safe)."""
    global _db_initialisee
    if _db_initialisee:
        return

    with _db_lock:
        if _db_initialisee:  # double-check
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
# PROTECTION DES ROUTES DEBUG
# =========================================================
def _secret_ok():
    """Vérifie le secret admin dans le header/query."""
    secret_attendu = os.environ.get("ADMIN_SECRET", "")
    if not secret_attendu:
        # Pas de secret configuré : routes debug désactivées
        return False
    fourni = request.args.get("secret") or request.headers.get("X-Admin-Secret")
    return fourni == secret_attendu


def admin_required(f):
    """Décorateur : bloque l'accès si le secret est absent/invalide."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _secret_ok():
            log_warning(
                message="Accès refusé à une route admin",
                module="FLASK",
                extra={
                    "route": request.path,
                    "ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent", "")[:100],
                },
            )
            return "🔒 Accès refusé. Secret manquant ou invalide.", 403
        return f(*args, **kwargs)
    return wrapper


# =========================================================
# MIDDLEWARE FLASK : capture TOUTES les erreurs HTTP
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
def _envoyer_message_securise(chat_id, texte, parse_mode=None):
    """Envoie un message en gérant la limite 4096."""
    limite = 4000
    if len(texte) <= limite:
        try:
            bot.send_message(chat_id, texte, parse_mode=parse_mode)
            return True
        except Exception as e:
            log_warning(
                message="Échec envoi message (fallback sans parse_mode)",
                module="NOTIFS",
                extra={"chat_id": chat_id, "parse_mode": parse_mode},
                exception=e,
            )
            try:
                bot.send_message(chat_id, texte)
                return True
            except Exception as e2:
                log_error(
                    message="Échec envoi message (double fallback)",
                    module="NOTIFS",
                    extra={"chat_id": chat_id},
                    exception=e2,
                )
                return False

    morceaux = [texte[i:i + limite] for i in range(0, len(texte), limite)]
    for morceau in morceaux:
        try:
            bot.send_message(chat_id, morceau, parse_mode=parse_mode)
        except Exception as e:
            log_warning(
                message="Échec envoi morceau",
                module="NOTIFS",
                extra={"chat_id": chat_id},
                exception=e,
            )
            try:
                bot.send_message(chat_id, morceau)
            except Exception as e2:
                log_error(
                    message="Échec envoi morceau (fallback)",
                    module="NOTIFS",
                    extra={"chat_id": chat_id},
                    exception=e2,
                )
                return False
        time.sleep(0.3)
    return True


def charger_modele_universel():
    """Charge les modèles si nécessaire."""
    from core.ml_model import global_model_data, charger_et_entrainer

    if global_model_data.get("modeles_par_competition") is not None:
        return True

    if charger_et_entrainer():
        log_info(
            f"Modèles chargés : {len(global_model_data['modeles_par_competition'])} compétitions",
            "BOOT",
        )
        return True

    log_warning("Impossible de charger les modèles.", "BOOT")
    return False


# =========================================================
# PERSISTANCE DES DERNIÈRES EXÉCUTIONS (scheduler)
# =========================================================
def _get_derniere_execution(cle, defaut=None):
    """Récupère la dernière date d'exécution d'une tâche (stockée en BDD)."""
    try:
        val = get_parametre(f"sched_{cle}", defaut)
        return val
    except Exception as e:
        log_warning(
            message=f"Impossible de lire sched_{cle}",
            module="SCHEDULER",
            exception=e,
        )
        return defaut


def _set_derniere_execution(cle, date_str):
    """Enregistre la date d'exécution en BDD."""
    try:
        set_parametre(f"sched_{cle}", date_str, f"Dernière exécution {cle}")
    except Exception as e:
        log_warning(
            message=f"Impossible d'écrire sched_{cle}",
            module="SCHEDULER",
            exception=e,
        )


# =========================================================
# TÂCHES AUTOMATIQUES
# =========================================================
def _mettre_a_jour_resultats():
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats
        total = mettre_a_jour_resultats()
        log_info(f"Résultats mis à jour : {total} matchs.", "SCHEDULER")
    except Exception as e:
        log_error(
            message="Erreur lors de la mise à jour des résultats",
            module="SCHEDULER",
            exception=e,
        )


def _telecharger_nouveaux_matchs():
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        log_info(f"Matchs téléchargés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error(
            message="Erreur lors du téléchargement des matchs",
            module="SCHEDULER",
            exception=e,
        )


def _nettoyer_vieilles_donnees():
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        log_info(f"Matchs de plus de 5 ans supprimés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error(
            message="Erreur nettoyage vieilles données",
            module="SCHEDULER",
            exception=e,
        )


def _envoyer_notifications():
    """Envoie les 3 meilleurs pronostics aux abonnés."""
    if not charger_modele_universel():
        return

    try:
        from core.daily_matches import get_matchs_du_jour
        matchs = get_matchs_du_jour()
    except Exception as e:
        log_error(
            message="Erreur récupération matchs pour notifications",
            module="NOTIFS",
            exception=e,
        )
        return

    if not matchs:
        return

    top_3 = sorted(matchs, key=lambda x: x["dc_pct"], reverse=True)[:3]
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    texte = f"🔥 **TOP 3 PRONOSTICS DU JOUR** 🔥\nDate : {date_str}\n\n"
    for i, m in enumerate(top_3, 1):
        texte += (
            f"{i}. **{m['home']} vs {m['away']}**\n"
            f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct'] * 100, 1)}%)\n"
            f"   🎯 BTTS : {round(m['btts'] * 100, 1)}% | "
            f"🥅 Over 2.5 : {round(m['over_25'] * 100, 1)}%\n\n"
        )

    users = get_utilisateurs_notifies()
    succes = 0
    echecs = 0
    for uid in users:
        if _envoyer_message_securise(uid, texte, parse_mode="Markdown"):
            succes += 1
        else:
            echecs += 1
        time.sleep(0.1)

    log_info(
        f"Notifications envoyées : {succes} succès, {echecs} échecs",
        "NOTIFS",
        extra={"succes": succes, "echecs": echecs},
    )


def _envoyer_coupons_premium():
    """Envoie les coupons aux Premium."""
    if not charger_modele_universel():
        return
    try:
        from core.paris_builder import generer_coupons_du_jour, formater_coupon
        from users import get_langue
        from users.db import db_fetchall

        data = generer_coupons_du_jour()
        coupons = data["coupons"]
        if not coupons:
            return

        rows = db_fetchall(
            "SELECT user_id FROM utilisateurs WHERE status = 'premium'",
            db_context={"table": "utilisateurs", "operation": "list_premium"},
        )
        premiums = [r[0] for r in rows] if rows else []

        for uid in premiums:
            langue = get_langue(uid)
            for coupon in coupons:
                texte = formater_coupon(coupon, langue, montrer_details=True)
                _envoyer_message_securise(uid, texte)
                time.sleep(0.1)
    except Exception as e:
        log_error(
            message="Erreur lors de l'envoi des coupons",
            module="COUPONS",
            exception=e,
        )


# =========================================================
# SCHEDULER
# =========================================================
def _scheduler_notifications():
    """Tâche de fond : toutes les tâches planifiées."""
    log_info("Scheduler démarré...", "SCHEDULER")

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5
            date_du_jour = now.strftime("%Y-%m-%d")

            # Heure de notification (paramétrable)
            try:
                heure_notif_val = get_parametre("notif_heure", "8")
                heure_notif = int(heure_notif_val) if str(heure_notif_val).isdigit() else 8
            except Exception:
                heure_notif = 8

            _initialiser_bdd_si_necessaire()

            # -------------------------------------------------
            # 02:00 — Mise à jour des résultats
            # -------------------------------------------------
            if now.hour == 2 and now.minute < 5:
                if _get_derniere_execution("maj_resultats") != date_du_jour:
                    log_info("Mise à jour des résultats...", "SCHEDULER")
                    _mettre_a_jour_resultats()
                    _set_derniere_execution("maj_resultats", date_du_jour)

            # -------------------------------------------------
            # 03:00 — Téléchargement matchs
            # -------------------------------------------------
            if now.hour == 3 and now.minute < 5:
                if _get_derniere_execution("telechargement") != date_du_jour:
                    log_info("Téléchargement des matchs...", "SCHEDULER")
                    _telecharger_nouveaux_matchs()
                    _set_derniere_execution("telechargement", date_du_jour)

            # -------------------------------------------------
            # 03:05 — Nettoyage vieilles données
            # -------------------------------------------------
            if now.hour == 3 and 5 <= now.minute < 10:
                if _get_derniere_execution("nettoyage_donnees") != date_du_jour:
                    log_info("Nettoyage des données > 5 ans...", "SCHEDULER")
                    _nettoyer_vieilles_donnees()
                    _set_derniere_execution("nettoyage_donnees", date_du_jour)

            # -------------------------------------------------
            # 03:10 — Nettoyage logs/paiements
            # -------------------------------------------------
            if now.hour == 3 and 10 <= now.minute < 15:
                if _get_derniere_execution("nettoyage_logs") != date_du_jour:
                    try:
                        from users import nettoyer_logs_anciens, nettoyer_paiements_anciens
                        nettoyer_logs_anciens(jours=30)
                        nettoyer_paiements_anciens(jours=90)
                        _set_derniere_execution("nettoyage_logs", date_du_jour)
                    except Exception as e:
                        log_error(
                            message="Erreur nettoyage logs/paiements",
                            module="SCHEDULER",
                            exception=e,
                        )

            # -------------------------------------------------
            # 07:00 — Bilan de la veille
            # -------------------------------------------------
            if now.hour == 7 and now.minute < 5:
                if _get_derniere_execution("verif_veille") != date_du_jour:
                    try:
                        from core.results_checker import verifier_resultats_veille
                        from core.canal_manager import publier_bilan_veille
                        bilan = verifier_resultats_veille()
                        if bilan.get("total", 0) > 0:
                            publier_bilan_veille(bot, bilan["texte"])
                        _set_derniere_execution("verif_veille", date_du_jour)
                    except Exception as e:
                        log_error(
                            message="Erreur vérif veille",
                            module="SCHEDULER",
                            exception=e,
                        )

            # -------------------------------------------------
            # heure_notif — Envoi notifications + canal
            # -------------------------------------------------
            if now.hour == heure_notif and now.minute < 5:
                if _get_derniere_execution("notifs_jour") != date_du_jour:
                    log_info("Envoi notifications du jour...", "SCHEDULER")
                    _envoyer_notifications()
                    _set_derniere_execution("notifs_jour", date_du_jour)

                    if est_weekend:
                        _envoyer_coupons_premium()

                    if _get_derniere_execution("canal_matchs") != date_du_jour:
                        try:
                            from core.canal_manager import publier_matchs_sur_canal
                            publier_matchs_sur_canal(bot)
                            _set_derniere_execution("canal_matchs", date_du_jour)
                        except Exception as e:
                            log_error(
                                message="Erreur publication canal matchs",
                                module="SCHEDULER",
                                exception=e,
                            )

            # -------------------------------------------------
            # 10:00 — Coupons semaine
            # -------------------------------------------------
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if _get_derniere_execution("coupons_semaine") != date_du_jour:
                    log_info("Envoi coupons semaine...", "SCHEDULER")
                    _envoyer_coupons_premium()
                    try:
                        from core.canal_manager import publier_coupons_sur_canal
                        publier_coupons_sur_canal(bot)
                        _set_derniere_execution("coupons_semaine", date_du_jour)
                    except Exception as e:
                        log_error(
                            message="Erreur publication coupons",
                            module="SCHEDULER",
                            exception=e,
                        )

            # -------------------------------------------------
            # 17:00 — Teasing canal
            # -------------------------------------------------
            if now.hour == 17 and now.minute < 5:
                if _get_derniere_execution("teasing") != date_du_jour:
                    try:
                        from core.canal_manager import publier_teasing
                        publier_teasing(bot)
                        _set_derniere_execution("teasing", date_du_jour)
                    except Exception as e:
                        log_error(
                            message="Erreur teasing",
                            module="SCHEDULER",
                            exception=e,
                        )

            time.sleep(60)
        except Exception as e:
            log_error(
                message="Erreur critique dans le scheduler, pause 60s",
                module="SCHEDULER",
                exception=e,
            )
            time.sleep(60)


def _lancer_scheduler_apres_delai():
    time.sleep(60)
    try:
        _scheduler_notifications()
    except Exception as e:
        log_critical(
            message="Le scheduler s'est arrêté prématurément",
            module="SCHEDULER",
            exception=e,
        )


# =========================================================
# ROUTES FLASK
# =========================================================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Point d'entrée Telegram."""
    try:
        _initialiser_bdd_si_necessaire()
    except Exception as e:
        log_critical(
            message="Impossible d'initialiser la BDD depuis le webhook",
            module="FLASK",
            exception=e,
        )
        return "DB init failed", 500

    try:
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        if not update:
            return "OK", 200

        def traiter_update():
            try:
                bot.process_new_updates([update])
            except Exception as e:
                log_error(
                    message="Erreur traitement update Telegram",
                    module="FLASK",
                    extra={"update_id": getattr(update, "update_id", "?")},
                    exception=e,
                )

        threading.Thread(target=traiter_update, daemon=True).start()
        return "OK", 200
    except Exception as e:
        log_error(
            message="Erreur parsing update Telegram",
            module="FLASK",
            exception=e,
        )
        return "OK", 200


@app.route("/")
def index():
    return "Bot operationnel !", 200


@app.route("/health")
def health():
    """Health check (retourne 200 si la DB répond)."""
    try:
        from users.db import db_fetchone
        row = db_fetchone("SELECT 1")
        if row:
            return "✅ OK", 200
        return "❌ DB muette", 503
    except Exception as e:
        log_error(
            message="Health check : DB inaccessible",
            module="FLASK",
            exception=e,
        )
        return "❌ DB inaccessible", 503


@app.route("/debug_env")
@admin_required
def debug_env():
    return (
        f"TURSO_URL : {'✅' if TURSO_URL else '❌'} ({len(TURSO_URL)})\n"
        f"TURSO_TOKEN : {'✅' if TURSO_TOKEN else '❌'} ({len(TURSO_TOKEN)})\n"
        f"TELEGRAM_TOKEN : {'✅' if TOKEN else '❌'} ({len(TOKEN)})\n"
        f"MODE_VITRINE : {MODE_VITRINE}\n"
        f"ADMIN_ID : {ADMIN_ID}"
    ), 200


@app.route("/init_db")
@admin_required
def init_db():
    global _db_initialisee
    try:
        from users.db import initialiser_tables, db_fetchall
        initialiser_tables()
        _db_initialisee = True
        rows = db_fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        noms = [r[0] for r in rows] if rows else []
        return f"✅ Tables ({len(noms)}) :\n" + "\n".join(noms), 200
    except Exception as e:
        log_error(
            message="Erreur /init_db",
            module="FLASK",
            exception=e,
        )
        return f"❌ Erreur : {e}", 500


@app.route("/webhook_info")
@admin_required
def webhook_info():
    try:
        res = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo", timeout=10
        )
        data = res.json()
        if not data.get("ok"):
            return f"❌ Erreur Telegram : {data}", 500
        info = data.get("result", {})
        return (
            f"🔗 URL : {info.get('url', '❌')}\n"
            f"📥 En attente : {info.get('pending_update_count', 0)}\n"
            f"🔧 Dernière erreur : {info.get('last_error_message', 'Aucune')}"
        ), 200
    except Exception as e:
        log_error(message="Erreur /webhook_info", module="FLASK", exception=e)
        return f"❌ {e}", 500


@app.route("/delete_webhook_pending")
@admin_required
def delete_webhook_pending():
    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true",
            timeout=10,
        )
        return "✅ Webhook supprimé et messages vidés.", 200
    except Exception as e:
        log_error(message="Erreur delete_webhook", module="FLASK", exception=e)
        return f"❌ {e}", 500


@app.route("/set_webhook")
@admin_required
def set_webhook():
    try:
        host = request.headers.get("Host", "prediction-football-209y.onrender.com")
        webhook_url = f"https://{host}/{TOKEN}"
        res = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}",
            timeout=10,
        )
        data = res.json()
        if data.get("ok"):
            return f"✅ Webhook défini : {webhook_url}", 200
        return f"❌ {data}", 500
    except Exception as e:
        log_error(message="Erreur set_webhook", module="FLASK", exception=e)
        return f"❌ {e}", 500


@app.route("/maj_resultats")
@admin_required
def maj_resultats():
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats
        total = mettre_a_jour_resultats()
        return f"✅ {total} matchs mis à jour.", 200
    except Exception as e:
        log_error(message="Erreur /maj_resultats", module="FLASK", exception=e)
        return f"❌ {e}", 500


@app.route("/telecharger")
@admin_required
def telecharger():
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        return f"✅ {total} matchs traités.", 200
    except Exception as e:
        log_error(message="Erreur /telecharger", module="FLASK", exception=e)
        return f"❌ {e}", 500


@app.route("/nettoyer")
@admin_required
def nettoyer():
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        return f"✅ {total} matchs > 5 ans supprimés.", 200
    except Exception as e:
        log_error(message="Erreur /nettoyer", module="FLASK", exception=e)
        return f"❌ {e}", 500


# =========================================================
# DÉMARRAGE
# =========================================================
log_info("Bot prêt (Lazy Loading activé).", "BOOT")

if not MODE_VITRINE:
    threading.Thread(target=_lancer_scheduler_apres_delai, daemon=True).start()
    log_info("Scheduler programmé.", "BOOT")
else:
    log_warning("Mode vitrine : scheduler désactivé.", "BOOT")
