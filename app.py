import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import threading
import telebot
from datetime import datetime, timezone, timedelta
from flask import Flask, request

from config import TOKEN
from users import initialiser_tables, get_utilisateurs_notifies
from telegram_bot.handlers import enregistrer_handlers


bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))


def _envoyer_notifications():
    try:
        from core.ml_model import global_model_data, get_top_pronostics_du_jour

        if not global_model_data.get('df'):
            from users import charger_modele_cache
            import io
            import joblib

            cache = charger_modele_cache()
            if not cache:
                print("⚠️ Notifications : pas de cache modèle")
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
            print("⚠️ Notifications : aucun pronostic disponible")
            return

        date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")

        texte = (
            f"╔══════════════════════════╗\n"
            f"║  🌅 *PRONOSTICS DU JOUR* ║\n"
            f"╚══════════════════════════╝\n\n"
            f"📅 _{date_str}_\n\n"
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
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 *{i}. {item['home']} vs {item['away']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Recommandé : *{meilleure[0]}* ({meilleure[1]}%)\n"
                f"⚽ Score probable : *{prono['best_score'][0]} - {prono['best_score'][1]}*\n\n"
            )

        texte += (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Tape une affiche pour plus de détails_\n"
            f"🔕 _Pour désactiver : /notif_off_"
        )

        users = get_utilisateurs_notifies()
        succes = 0
        echecs = 0

        for uid in users:
            try:
                bot.send_message(uid, texte, parse_mode="Markdown")
                succes += 1
                time.sleep(0.1)
            except Exception:
                echecs += 1

        print(f"📬 Notifications envoyées : {succes} succès, {echecs} échecs")

    except Exception as e:
        print(f"⚠️ Erreur envoi notifications : {e}")


def _scheduler_notifications():
    print("📅 Scheduler notifications démarré...")
    derniere_date_envoi = None

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)

            if now.hour == 8 and now.minute < 5:
                date_du_jour = now.strftime("%Y-%m-%d")
                if derniere_date_envoi != date_du_jour:
                    print(f"📬 Envoi des notifications du {date_du_jour}...")
                    _envoyer_notifications()
                    derniere_date_envoi = date_du_jour

            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Erreur scheduler : {e}")
            time.sleep(60)


threading.Thread(target=_scheduler_notifications, daemon=True).start()


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route('/')
def index():
    return "Bot opérationnel !", 200


initialiser_tables()
print("🚀 Bot prêt (init différée + notifications actives).")
