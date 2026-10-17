import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import threading
import telebot
from datetime import datetime, timezone, timedelta
from flask import Flask, request

from config import TOKEN
from users import initialiser_tables, get_utilisateurs_notifies, est_banni, est_administrateur, get_parametre
from telegram_bot.handlers import enregistrer_handlers
from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.inline_handlers import enregistrer_inline_handlers

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

enregistrer_admin_handlers(bot)
enregistrer_inline_handlers(bot)
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))

# ... (La fonction _envoyer_notifications reste IDENTIQUE) ...
# ... (La fonction _envoyer_coupons_premium reste IDENTIQUE) ...

# =========================================================
# SCHEDULER (CORRIGÉ avec lecture BDD et Canal)
# =========================================================
def _scheduler_notifications():
    print("Scheduler notifications demarre...")
    derniere_date_envoi = None
    derniere_date_coupons_semaine = None
    derniere_date_coupons_weekend = None
    derniere_date_canal = None
    dernier_nettoyage = None

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5

            # LECTURE DYNAMIQUE DE L'HEURE
            try:
                heure_notif = int(get_parametre("notif_heure", 8))
            except:
                heure_notif = 8

            # Notifications (Heure dynamique)
            if now.hour == heure_notif and now.minute < 5:
                date_du_jour = now.strftime("%Y-%m-%d")
                if derniere_date_envoi != date_du_jour:
                    print(f"Envoi des notifications du {date_du_jour}...")
                    _envoyer_notifications()
                    derniere_date_envoi = date_du_jour

                    if est_weekend:
                        print("Weekend : envoi des coupons...")
                        _envoyer_coupons_premium()
                        derniere_date_coupons_weekend = date_du_jour
                        
                    # NOUVEAU : Publication sur le canal en même temps
                    if derniere_date_canal != date_du_jour:
                        from core.canal_manager import publier_matchs_sur_canal
                        publier_matchs_sur_canal(bot)
                        derniere_date_canal = date_du_jour

            # Coupons Semaine à 10h
            if not est_weekend and now.hour == 10 and now.minute < 5:
                date_du_jour = now.strftime("%Y-%m-%d")
                if derniere_date_coupons_semaine != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    _envoyer_coupons_premium()
                    derniere_date_coupons_semaine = date_du_jour

            # Nettoyage à 3h
            if now.hour == 3 and now.minute < 5:
                date_du_jour = now.strftime("%Y-%m-%d")
                if dernier_nettoyage != date_du_jour:
                    print(f"Nettoyage auto du {date_du_jour}...")
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


threading.Thread(target=_scheduler_notifications, daemon=True).start()


# =========================================================
# WEBHOOK (CORRIGÉ avec Mode Maintenance)
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)

    try:
        if update.message:
            user_id = update.message.from_user.id
            
            # 1. Vérification Banni
            if est_banni(user_id) and not est_administrateur(user_id):
                return "OK", 200
                
            # 2. Vérification Mode Maintenance
            mode_maintenance = get_parametre("mode_maintenance", "off")
            if mode_maintenance == "on" and not est_administrateur(user_id):
                bot.send_message(user_id, "🛠️ Le bot est actuellement en maintenance. Veuillez réessayer plus tard.")
                return "OK", 200
                
    except Exception:
        pass

    bot.process_new_updates([update])
    return "OK", 200


@app.route('/')
def index():
    return "Bot operationnel !", 200


initialiser_tables()
print("Bot pret (init differee + notifications + canal + maintenance).")
