import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import threading
import telebot
from datetime import datetime, timezone, timedelta
from flask import Flask, request

from config import TOKEN
from users import initialiser_tables, get_utilisateurs_notifies, est_banni
from telegram_bot.handlers import enregistrer_handlers
from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.inline_handlers import enregistrer_inline_handlers


bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ⚠️ ORDRE CRUCIAL
enregistrer_admin_handlers(bot)
enregistrer_inline_handlers(bot)
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))


# =========================================================
# NOTIFICATIONS QUOTIDIENNES
# =========================================================
def _envoyer_notifications():
    try:
        from core.ml_model import global_model_data, get_top_pronostics_du_jour

        if not global_model_data.get('df'):
            from users import charger_modele_cache
            import io
            import joblib

            cache = charger_modele_cache()
            if not cache:
                print("Notifications : pas de cache modele")
                return

            modele_bytes, precision, nb_matchs = cache
            buffer = io.BytesIO(modele_bytes)
            donnees = joblib.load(buffer)

            global_model_data['df'] = donnees['df']
            global_model_data['teams'] = donnees['teams']
            global_model_data['team_to_code'] = donnees['team_to_code']
            global_model_data['team_global_stats'] = donnees['team_global_stats']
            global_model_data['precision'] = precision
            global_model_data['model'] = donnees['model']
            global_model_data['features'] = donnees['features']

        top = get_top_pronostics_du_jour(nb=3)

        if not top:
            print("Notifications : aucun pronostic disponible")
            return

        date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

        texte = (
            f"PRONOSTICS DU JOUR\n"
            f"Date : {date_str}\n\n"
        )

        for i, item in enumerate(top, 1):
            prono = item['prono']
            dc_1x = round(prono['dc_1x'] * 100, 1)
            dc_x2 = round(prono['dc_x2'] * 100, 1)
            dc_12 = round(prono['dc_12'] * 100, 1)

            meilleure = max(
                [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)],
                key=lambda x: x[1]
            )

            texte += (
                f"------------------------\n"
                f"{i}. {item['home']} vs {item['away']}\n"
                f"------------------------\n"
                f"Recommande : {meilleure[0]} ({meilleure[1]}%)\n"
                f"Score probable : {prono['best_score'][0]} - {prono['best_score'][1]}\n\n"
            )

        texte += (
            f"------------------------\n"
            f"Tape une affiche pour plus de details\n"
            f"Pour desactiver : /notif_off"
        )

        users = get_utilisateurs_notifies()
        succes = 0
        echecs = 0

        for uid in users:
            try:
                bot.send_message(uid, texte)
                succes += 1
                time.sleep(0.1)
            except Exception:
                echecs += 1

        print(f"Notifications envoyees : {succes} succes, {echecs} echecs")

    except Exception as e:
        print(f"Erreur envoi notifications : {e}")


# =========================================================
# ENVOI COUPONS PREMIUM
# =========================================================
def _envoyer_coupons_premium():
    """Envoie les coupons à tous les Premium."""
    from core.paris_builder import generer_coupons_du_jour, formater_coupon
    from users import get_langue
    from users.db import get_connection

    try:
        data = generer_coupons_du_jour()
        coupons = data['coupons']

        if not coupons:
            print("Aucun coupon à envoyer")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id FROM utilisateurs
            WHERE status = 'premium'
            AND (date_expiration IS NULL OR date_expiration > NOW())
        """)
        premiums = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        succes = 0
        for uid in premiums:
            try:
                langue = get_langue(uid)

                for coupon in coupons:
                    texte = formater_coupon(coupon, langue, montrer_details=True)
                    bot.send_message(uid, texte)
                    time.sleep(0.1)

                succes += 1
            except Exception as e:
                print(f"Erreur envoi coupons à {uid} : {e}")

        print(f"📤 Coupons envoyés à {succes} Premium(s)")

    except Exception as e:
        print(f"Erreur envoi coupons : {e}")


# =========================================================
# SCHEDULER
# =========================================================
def _scheduler_notifications():
    print("Scheduler notifications demarre...")
    derniere_date_envoi = None
    derniere_date_coupons_semaine = None
    derniere_date_coupons_weekend = None
    dernier_nettoyage = None

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5

            # Notifications à 8h
            if now.hour == 8 and now.minute < 5:
                date_du_jour = now.strftime("%Y-%m-%d")
                if derniere_date_envoi != date_du_jour:
                    print(f"Envoi des notifications du {date_du_jour}...")
                    _envoyer_notifications()
                    derniere_date_envoi = date_du_jour

                    # Weekend : envoyer les coupons juste après
                    if est_weekend:
                        print("Weekend : envoi des coupons...")
                        _envoyer_coupons_premium()
                        derniere_date_coupons_weekend = date_du_jour

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
# WEBHOOK
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)

    try:
        if update.message:
            user_id = update.message.from_user.id
            from users import est_administrateur
            if est_banni(user_id) and not est_administrateur(user_id):
                return "OK", 200
    except Exception:
        pass

    bot.process_new_updates([update])
    return "OK", 200


@app.route('/')
def index():
    return "Bot operationnel !", 200


initialiser_tables()
print("Bot pret (init differee + notifications + coupons + paiements + parrainage).")
