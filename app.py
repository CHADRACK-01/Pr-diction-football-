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

# Initialisation du bot et de l'application Flask
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Enregistrement de tous les handlers
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))

# Variable globale pour éviter d'initialiser la BDD 1000 fois
_db_initialisee = False


def _initialiser_bdd_si_necessaire():
    """Crée les tables Turso une seule fois."""
    global _db_initialisee
    if _db_initialisee:
        return
    try:
        from users.db import initialiser_tables
        print("🔧 Initialisation BDD (lazy)...")
        initialiser_tables()
        _db_initialisee = True
        print("✅ BDD initialisée.")
    except Exception as e:
        print(f"⚠️ Erreur init BDD : {e}")


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
        print(f"✅ Modèles chargés : {len(global_model_data['modeles_par_competition'])} compétitions")
        return True
    else:
        print("⚠️ Impossible de charger les modèles.")
        return False


def _envoyer_notifications():
    if not charger_modele_universel():
        return
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
        except Exception:
            pass


def _envoyer_coupons_premium():
    if not charger_modele_universel():
        return
    from core.paris_builder import generer_coupons_du_jour, formater_coupon
    from users import get_langue
    from users.db import get_connection
    data = generer_coupons_du_jour()
    coupons = data['coupons']
    if not coupons:
        return
    try:
        conn = get_connection()
        cur = conn.execute("SELECT user_id FROM utilisateurs WHERE status = 'premium'")
        premiums = [row[0] for row in cur.fetchall()]
        conn.close()
    except Exception:
        return
    for uid in premiums:
        langue = get_langue(uid)
        for coupon in coupons:
            texte = formater_coupon(coupon, langue, montrer_details=True)
            _envoyer_message_securise(uid, texte)
            time.sleep(0.1)


def _scheduler_notifications():
    print("Scheduler démarré...")
    dernier_nettoyage = None
    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            date_du_jour = now.strftime("%Y-%m-%d")
            
            # Initialiser la BDD si pas encore fait
            _initialiser_bdd_si_necessaire()
            
            # Nettoyage à 3h
            if now.hour == 3 and now.minute < 5:
                if dernier_nettoyage != date_du_jour:
                    try:
                        from users import nettoyer_logs_anciens, nettoyer_paiements_anciens
                        nettoyer_logs_anciens(jours=30)
                        nettoyer_paiements_anciens(jours=90)
                    except Exception as e:
                        print(f"Erreur nettoyage : {e}")
                    dernier_nettoyage = date_du_jour
            time.sleep(60)
        except Exception as e:
            print(f"Erreur scheduler : {e}")
            time.sleep(60)


def _lancer_scheduler_apres_delai():
    time.sleep(60)
    _scheduler_notifications()


# =========================================================
# ROUTES FLASK
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Point d'entrée Telegram avec initialisation lazy."""
    # 1. Initialiser la BDD au premier message reçu
    _initialiser_bdd_si_necessaire()

    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)

    if update.message:
        user_id = update.message.from_user.id
        try:
            is_banned = est_banni(user_id)
            is_admin = est_administrateur(user_id)
            mode_maintenance = get_parametre("mode_maintenance", "off")
        except Exception:
            is_banned = False
            is_admin = False
            mode_maintenance = "off"
            
        if is_banned and not is_admin:
            return "OK", 200
            
        if mode_maintenance == "on" and not is_admin:
            try:
                bot.send_message(user_id, "🛠️ Maintenance en cours.")
            except Exception:
                pass
            return "OK", 200

    try:
        bot.process_new_updates([update])
    except Exception as e:
        print(f"❌ Erreur update : {e}")
        import traceback
        traceback.print_exc()
    
    return "OK", 200


@app.route('/')
def index():
    return "Bot operationnel !", 200


@app.route('/health')
def health():
    """Vérifie Turso."""
    from users.db import get_connection
    try:
        conn = get_connection()
        result = conn.execute("SELECT 1").fetchone()
        conn.close()
        return "✅ Turso OK" if result else "❌ Turso muet", 200
    except Exception as e:
        return f"❌ Turso erreur : {e}", 500


@app.route('/debug_env')
def debug_env():
    url_ok = "✅" if TURSO_URL else "❌"
    token_ok = "✅" if TURSO_TOKEN else "❌"
    token_ok_short = "✅" if TOKEN else "❌"
    return f"TURSO_URL : {url_ok} ({len(TURSO_URL)})\nTURSO_TOKEN : {token_ok} ({len(TURSO_TOKEN)})\nTELEGRAM_TOKEN : {token_ok_short} ({len(TOKEN)})\nMODE_VITRINE : {MODE_VITRINE}", 200


@app.route('/init_db')
def init_db():
    """Crée les tables manuellement."""
    global _db_initialisee
    from users.db import initialiser_tables, get_connection
    try:
        initialiser_tables()
        _db_initialisee = True
        conn = get_connection()
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        noms = [r[0] for r in result]
        conn.close()
        return f"✅ Tables créées :\n" + "\n".join(noms), 200
    except Exception as e:
        import traceback
        return f"❌ Erreur : {e}\n{traceback.format_exc()}", 500


@app.route('/webhook_info')
def webhook_info():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        res = requests.get(url, timeout=10)
        data = res.json()
        if not data.get('ok'):
            return f"❌ Erreur Telegram : {data}", 500
        info = data.get('result', {})
        texte = f"📡 INFOS WEBHOOK\n\n🔗 URL : {info.get('url', '❌')}\n📥 En attente : {info.get('pending_update_count', 0)}\n🔧 Dernière erreur : {info.get('last_error_message', 'Aucune')}\n"
        return texte, 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/delete_webhook_pending')
def delete_webhook_pending():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
        res = requests.get(url, timeout=10)
        return "✅ Webhook supprimé et messages vidés !", 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/set_webhook')
def set_webhook():
    try:
        host = request.headers.get('Host', 'prediction-football-209y.onrender.com')
        webhook_url = f"https://{host}/{TOKEN}"
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get('ok'):
            return f"✅ Webhook défini : {webhook_url}", 200
        return f"❌ Erreur : {data}", 500
    except Exception as e:
        return f"❌ Erreur : {e}", 500


# =========================================================
# INITIALISATION AU DÉMARRAGE (LAZY)
# =========================================================
# ⚠️ On ne fait RIEN au démarrage pour que Render considère le bot comme "prêt" immédiatement.
print("✅ Bot prêt (Lazy Loading activé).")

if not MODE_VITRINE:
    threading.Thread(target=_lancer_scheduler_apres_delai, daemon=True).start()
    print("✅ Scheduler programmé.")
else:
    print("⚠️ Mode vitrine : scheduler désactivé.")
