import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import threading
import telebot
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, request

# =========================================================
# ⚠️ SÉCURITÉ GLOBALE
# =========================================================
from core.utils.error_handler import activer_capture_globale
activer_capture_globale()

from config import TOKEN, MODE_VITRINE, TURSO_URL, TURSO_TOKEN
from users import (
    get_utilisateurs_notifies, est_banni, 
    est_administrateur, get_parametre
)
from telegram_bot.handlers import enregistrer_handlers
from core.utils.logs import log_info, log_error, log_warning

# Initialisation du bot et de l'application Flask
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Enregistrement de tous les handlers
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))

# Variable globale pour l'initialisation différée de la BDD
_db_initialisee = False


def _initialiser_bdd_si_necessaire():
    """Crée les tables Turso une seule fois (Lazy Loading)."""
    global _db_initialisee
    if _db_initialisee:
        return
    from users.db import initialiser_tables
    log_info("Initialisation BDD (lazy)...", "BOOT")
    initialiser_tables()
    _db_initialisee = True
    log_info("BDD initialisée.", "BOOT")


# =========================================================
# MIDDLEWARE FLASK : Capture TOUTES les erreurs HTTP
# =========================================================
@app.errorhandler(Exception)
def gerer_erreur_globale(e):
    """Capture toutes les erreurs Flask et les envoie à l'admin."""
    log_error(
        message=f"Erreur Flask non gérée : {e}",
        module="FLASK",
        exception=e
    )
    return f"❌ Erreur interne : {e}", 500


# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================
def _envoyer_message_securise(chat_id, texte, parse_mode=None):
    """Envoie un message en gérant la limite de 4096 caractères."""
    limite = 4000
    if len(texte) <= limite:
        bot.send_message(chat_id, texte, parse_mode=parse_mode)
    else:
        morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
        for morceau in morceaux:
            bot.send_message(chat_id, morceau, parse_mode=parse_mode)
            time.sleep(0.3)


def charger_modele_universel():
    """Charge les modèles depuis Turso."""
    from core.ml_model import global_model_data, charger_et_entrainer
    
    if global_model_data.get('modeles_par_competition') is not None:
        return True
        
    charger_et_entrainer()
    
    if global_model_data.get('modeles_par_competition') is not None:
        log_info(f"Modèles chargés : {len(global_model_data['modeles_par_competition'])} compétitions", "BOOT")
        return True
    else:
        log_warning("Impossible de charger les modèles.", "BOOT")
        return False


# =========================================================
# TÂCHES AUTOMATIQUES
# =========================================================
def _mettre_a_jour_resultats():
    """Met à jour les scores des matchs terminés."""
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats
        total = mettre_a_jour_resultats()
        log_info(f"Résultats mis à jour : {total} matchs.", "SCHEDULER")
    except Exception as e:
        log_error("Erreur lors de la mise à jour des résultats", "SCHEDULER", exception=e)


def _telecharger_nouveaux_matchs():
    """Télécharge les nouveaux matchs à venir."""
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        log_info(f"Nouveaux matchs téléchargés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error("Erreur lors du téléchargement des matchs", "SCHEDULER", exception=e)


def _nettoyer_vieilles_donnees():
    """Supprime les matchs de plus de 5 ans."""
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        log_info(f"Matchs de plus de 5 ans supprimés : {total}.", "SCHEDULER")
    except Exception as e:
        log_error("Erreur lors du nettoyage des vieilles données", "SCHEDULER", exception=e)


def _envoyer_notifications():
    """Envoie les meilleurs pronostics du jour aux utilisateurs abonnés."""
    if not charger_modele_universel():
        return
    try:
        from core.daily_matches import get_matchs_du_jour
        matchs = get_matchs_du_jour()
        if not matchs:
            return
        top_3 = sorted(matchs, key=lambda x: x['dc_pct'], reverse=True)[:3]
        date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
        texte = f"🔥 **TOP 3 PRONOSTICS DU JOUR** 🔥\nDate : {date_str}\n\n"
        for i, m in enumerate(top_3, 1):
            texte += f"{i}. **{m['home']} vs {m['away']}**\n   🛡️ DC : {m['dc_label']} ({round(m['dc_pct']*100, 1)}%)\n   🎯 BTTS : {round(m['btts']*100, 1)}% | 🥅 Over 2.5 : {round(m['over_25']*100, 1)}%\n\n"
        users = get_utilisateurs_notifies()
        for uid in users:
            try:
                _envoyer_message_securise(uid, texte, parse_mode='Markdown')
                time.sleep(0.1)
            except Exception as e:
                log_warning(f"Impossible d'envoyer la notif à {uid} : {e}", "NOTIFS")
    except Exception as e:
        log_error("Erreur lors de l'envoi des notifications", "NOTIFS", exception=e)


def _envoyer_coupons_premium():
    """Envoie les coupons aux Premium."""
    if not charger_modele_universel():
        return
    try:
        from core.paris_builder import generer_coupons_du_jour, formater_coupon
        from users import get_langue
        from users.db import get_connection
        
        data = generer_coupons_du_jour()
        coupons = data['coupons']
        if not coupons:
            return
        
        conn = get_connection()
        cur = conn.execute("SELECT user_id FROM utilisateurs WHERE status = 'premium'")
        premiums = [row[0] for row in cur.fetchall()]
        conn.close()
        
        for uid in premiums:
            langue = get_langue(uid)
            for coupon in coupons:
                texte = formater_coupon(coupon, langue, montrer_details=True)
                try:
                    _envoyer_message_securise(uid, texte)
                    time.sleep(0.1)
                except Exception as e:
                    log_warning(f"Impossible d'envoyer le coupon à {uid} : {e}", "COUPONS")
    except Exception as e:
        log_error("Erreur lors de l'envoi des coupons", "COUPONS", exception=e)


# =========================================================
# SCHEDULER PRINCIPAL
# =========================================================
def _scheduler_notifications():
    """Tâche de fond qui gère TOUS les envois automatiques."""
    log_info("Scheduler démarré...", "SCHEDULER")
    
    # Variables pour éviter d'exécuter deux fois la même tâche le même jour
    derniere_maj_resultats = None
    dernier_telechargement = None
    dernier_nettoyage_donnees = None
    dernier_nettoyage_logs = None
    derniere_verif_resultats = None
    derniere_date_envoi = None
    derniere_date_coupons_semaine = None
    derniere_date_coupons_weekend = None
    derniere_date_canal = None
    derniere_date_teasing = None

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5
            date_du_jour = now.strftime("%Y-%m-%d")

            # Récupération de l'heure de notification (paramètre dynamique)
            try:
                heure_notif_val = get_parametre("notif_heure", "8")
                heure_notif = int(heure_notif_val) if str(heure_notif_val).isdigit() else 8
            except Exception:
                heure_notif = 8

            _initialiser_bdd_si_necessaire()

            # =========================================================
            # 02:00 : Mise à jour des résultats
            # =========================================================
            if now.hour == 2 and now.minute < 5:
                if derniere_maj_resultats != date_du_jour:
                    log_info("Mise à jour des résultats des matchs passés...", "SCHEDULER")
                    _mettre_a_jour_resultats()
                    derniere_maj_resultats = date_du_jour

            # =========================================================
            # 03:00 : Téléchargement des nouveaux matchs
            # =========================================================
            if now.hour == 3 and now.minute < 5:
                if dernier_telechargement != date_du_jour:
                    log_info("Téléchargement des nouveaux matchs...", "SCHEDULER")
                    _telecharger_nouveaux_matchs()
                    dernier_telechargement = date_du_jour

            # =========================================================
            # 03:05 : Nettoyage des vieilles données (> 5 ans)
            # =========================================================
            if now.hour == 3 and 5 <= now.minute < 10:
                if dernier_nettoyage_donnees != date_du_jour:
                    log_info("Nettoyage des données de plus de 5 ans...", "SCHEDULER")
                    _nettoyer_vieilles_donnees()
                    dernier_nettoyage_donnees = date_du_jour

            # =========================================================
            # 03:10 : Nettoyage des logs et paiements
            # =========================================================
            if now.hour == 3 and 10 <= now.minute < 15:
                if dernier_nettoyage_logs != date_du_jour:
                    log_info("Nettoyage des logs et paiements...", "SCHEDULER")
                    try:
                        from users import nettoyer_logs_anciens, nettoyer_paiements_anciens
                        nettoyer_logs_anciens(jours=30)
                        nettoyer_paiements_anciens(jours=90)
                    except Exception as e:
                        log_error("Erreur lors du nettoyage des logs", "SCHEDULER", exception=e)
                    dernier_nettoyage_logs = date_du_jour

            # =========================================================
            # 07:00 : Vérification des résultats de la veille (bilan canal)
            # =========================================================
            if now.hour == 7 and now.minute < 5:
                if derniere_verif_resultats != date_du_jour:
                    log_info("Vérification des résultats de la veille...", "SCHEDULER")
                    try:
                        from core.results_checker import verifier_resultats_veille
                        from core.canal_manager import publier_bilan_veille
                        bilan = verifier_resultats_veille()
                        if bilan.get('total', 0) > 0:
                            publier_bilan_veille(bot, bilan['texte'])
                    except Exception as e:
                        log_error("Erreur vérif résultats", "SCHEDULER", exception=e)
                    derniere_verif_resultats = date_du_jour

            # =========================================================
            # 08:00 : Envoi des notifications
            # =========================================================
            if now.hour == heure_notif and now.minute < 5:
                if derniere_date_envoi != date_du_jour:
                    log_info("Envoi des notifications du jour...", "SCHEDULER")
                    _envoyer_notifications()
                    derniere_date_envoi = date_du_jour
                    
                    if est_weekend:
                        _envoyer_coupons_premium()
                        derniere_date_coupons_weekend = date_du_jour
                        
                    if derniere_date_canal != date_du_jour:
                        try:
                            from core.canal_manager import publier_matchs_sur_canal
                            publier_matchs_sur_canal(bot)
                        except Exception as e:
                            log_error("Erreur publication canal", "SCHEDULER", exception=e)
                        derniere_date_canal = date_du_jour

            # =========================================================
            # 10:00 : Coupons en semaine
            # =========================================================
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if derniere_date_coupons_semaine != date_du_jour:
                    log_info("Envoi des coupons (semaine)...", "SCHEDULER")
                    _envoyer_coupons_premium()
                    try:
                        from core.canal_manager import publier_coupons_sur_canal
                        publier_coupons_sur_canal(bot)
                    except Exception as e:
                        log_error("Erreur publication coupons", "SCHEDULER", exception=e)
                    derniere_date_coupons_semaine = date_du_jour

            # =========================================================
            # 17:00 : Teasing canal
            # =========================================================
            if now.hour == 17 and now.minute < 5:
                if derniere_date_teasing != date_du_jour:
                    log_info("Publication du teasing sur le canal...", "SCHEDULER")
                    try:
                        from core.canal_manager import publier_teasing
                        publier_teasing(bot)
                    except Exception as e:
                        log_error("Erreur teasing", "SCHEDULER", exception=e)
                    derniere_date_teasing = date_du_jour

            time.sleep(60)
        except Exception as e:
            log_error("Erreur scheduler", "SCHEDULER", exception=e)
            time.sleep(60)


def _lancer_scheduler_apres_delai():
    time.sleep(60)
    _scheduler_notifications()


# =========================================================
# ROUTES FLASK
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Point d'entrée Telegram."""
    _initialiser_bdd_si_necessaire()

    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)

    def traiter_update():
        bot.process_new_updates([update])

    threading.Thread(target=traiter_update, daemon=True).start()
    return "OK", 200


@app.route('/')
def index():
    return "Bot operationnel !", 200


@app.route('/health')
def health():
    from users.db import get_connection
    conn = get_connection()
    result = conn.execute("SELECT 1").fetchone()
    conn.close()
    return "✅ Turso OK" if result else "❌ Turso muet", 200


@app.route('/debug_env')
def debug_env():
    url_ok = "✅" if TURSO_URL else "❌"
    token_ok = "✅" if TURSO_TOKEN else "❌"
    token_ok_short = "✅" if TOKEN else "❌"
    return f"TURSO_URL : {url_ok} ({len(TURSO_URL)})\nTURSO_TOKEN : {token_ok} ({len(TURSO_TOKEN)})\nTELEGRAM_TOKEN : {token_ok_short} ({len(TOKEN)})\nMODE_VITRINE : {MODE_VITRINE}", 200


@app.route('/init_db')
def init_db():
    global _db_initialisee
    from users.db import initialiser_tables, get_connection
    initialiser_tables()
    _db_initialisee = True
    conn = get_connection()
    result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    noms = [r[0] for r in result]
    conn.close()
    return f"✅ Tables créées :\n" + "\n".join(noms), 200


@app.route('/webhook_info')
def webhook_info():
    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    res = requests.get(url, timeout=10)
    data = res.json()
    if not data.get('ok'):
        return f"❌ Erreur Telegram : {data}", 500
    info = data.get('result', {})
    texte = f"📡 INFOS WEBHOOK\n\n🔗 URL : {info.get('url', '❌')}\n📥 En attente : {info.get('pending_update_count', 0)}\n🔧 Dernière erreur : {info.get('last_error_message', 'Aucune')}\n"
    return texte, 200


@app.route('/delete_webhook_pending')
def delete_webhook_pending():
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
    requests.get(url, timeout=10)
    return "✅ Webhook supprimé et messages vidés !", 200


@app.route('/set_webhook')
def set_webhook():
    host = request.headers.get('Host', 'prediction-football-209y.onrender.com')
    webhook_url = f"https://{host}/{TOKEN}"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    res = requests.get(url, timeout=10)
    data = res.json()
    if data.get('ok'):
        return f"✅ Webhook défini : {webhook_url}", 200
    return f"❌ Erreur : {data}", 500


# =========================================================
# ROUTES DE DEBUG MANUEL
# =========================================================
@app.route('/maj_resultats')
def maj_resultats():
    """Déclenche manuellement la mise à jour des résultats."""
    try:
        from scripts.mettre_a_jour_resultats import mettre_a_jour_resultats
        total = mettre_a_jour_resultats()
        return f"✅ {total} matchs mis à jour. Regarde les logs.", 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/telecharger')
def telecharger():
    """Déclenche manuellement le téléchargement des matchs."""
    try:
        from scripts.telecharger_matchs import telecharger_tout
        total = telecharger_tout()
        return f"✅ {total} matchs traités. Regarde les logs.", 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/nettoyer')
def nettoyer():
    """Déclenche manuellement le nettoyage des vieilles données."""
    try:
        from users.matchs import nettoyer_vieilles_donnees
        total = nettoyer_vieilles_donnees(annees=5)
        return f"✅ {total} matchs de plus de 5 ans supprimés.", 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


# =========================================================
# INITIALISATION AU DÉMARRAGE (LAZY)
# =========================================================
log_info("Bot prêt (Lazy Loading activé).", "BOOT")

if not MODE_VITRINE:
    threading.Thread(target=_lancer_scheduler_apres_delai, daemon=True).start()
    log_info("Scheduler programmé.", "BOOT")
else:
    log_warning("Mode vitrine : scheduler désactivé.", "BOOT")
