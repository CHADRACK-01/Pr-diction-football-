import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import io
import joblib
import time
import threading
import telebot
from datetime import datetime, timezone, timedelta
from flask import Flask, request

from config import TOKEN
from users import (
    initialiser_tables, get_utilisateurs_notifies, est_banni, 
    est_administrateur, get_parametre
)
from telegram_bot.handlers import enregistrer_handlers

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))


def _envoyer_message_securise(chat_id, texte, parse_mode=None):
    limite = 4000
    try:
        if len(texte) <= limite:
            bot.send_message(chat_id, texte, parse_mode=parse_mode)
        else:
            morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
            for morceau in morceaux:
                bot.send_message(chat_id, morceau, parse_mode=parse_mode)
                time.sleep(0.3)
    except Exception as e:
        print(f"⚠️ Erreur envoi message sécurisé à {chat_id} : {e}")


def charger_modele_universel():
    from core.ml_model import global_model_data
    if global_model_data.get('model') is not None:
        return True
    try:
        from users import charger_modele_cache
        cache = charger_modele_cache()
        if not cache:
            print("❌ Aucun modèle en cache.")
            return False
        modele_bytes, precision, nb_matchs = cache
        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)
        global_model_data.update(donnees)
        global_model_data['precision'] = precision
        global_model_data['_tables_initialisees'] = True
        print(f"✅ Modèle chargé : {type(global_model_data['model']).__name__} (Précision : {round(precision*100, 2)}%)")
        return True
    except Exception as e:
        print(f"⚠️ Erreur chargement modèle : {e}")
        return False


def _envoyer_notifications():
    try:
        from core.ml_model import get_top_pronostics_du_jour
        if not charger_modele_universel():
            print("Notifications : impossible de charger le modèle.")
            return

        top = get_top_pronostics_du_jour(nb=15)
        if not top:
            print("Notifications : aucun pronostic disponible")
            return

        date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
        texte = f"🔥 PRONOSTICS VALUE BET DU JOUR 🔥\nDate : {date_str}\n\n"
        
        compte = 0
        for item in top:
            prono = item['prono']
            analyse = prono.get('analyse_pari')
            if not analyse: 
                continue
                
            if analyse['cote_bot'] >= 1.25 and analyse['proba'] >= 0.65:
                compte += 1
                texte += (
                    f"------------------------\n"
                    f"{compte}. {item['home']} vs {item['away']}\n"
                    f"✅ Reco : {analyse['label']} ({round(analyse['proba']*100, 1)}%)\n"
                    f"💰 Cote Bot : {analyse['cote_bot']}\n"
                )
                if analyse['cote_book']:
                    texte += f"🏢 Cote Book : {analyse['cote_book']}\n"
                    if analyse['is_value']:
                        texte += f"🔥 VALUE BET !\n"
                texte += f"⚽ Score probable : {prono['best_score'][0]} - {prono['best_score'][1]}\n\n"
            
            if compte >= 3: 
                break

        if compte == 0:
            print("Notifications : Aucun Value Bet trouvé aujourd'hui.")
            return
            
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


def _envoyer_coupons_premium():
    from core.paris_builder import generer_coupons_du_jour, formater_coupon
    from users import get_langue
    from users.db import get_connection

    try:
        if not charger_modele_universel():
            print("Coupons : impossible de charger le modèle.")
            return

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
                    _envoyer_message_securise(uid, texte)
                    time.sleep(0.1)
                succes += 1
            except Exception as e:
                print(f"Erreur envoi coupons à {uid} : {e}")

        print(f"📤 Coupons envoyés à {succes} Premium(s)")

    except Exception as e:
        print(f"Erreur envoi coupons : {e}")


def _scheduler_notifications():
    print("Scheduler demarre...")
    derniere_date_envoi = None
    derniere_date_coupons_semaine = None
    derniere_date_coupons_weekend = None
    derniere_date_canal = None
    derniere_date_teasing = None
    dernier_nettoyage = None
    derniere_verif_resultats = None

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5
            date_du_jour = now.strftime("%Y-%m-%d")

            try:
                heure_notif = int(get_parametre("notif_heure", 8))
            except:
                heure_notif = 8

            # 1. Vérification des résultats de la veille (à 7h)
            if now.hour == 7 and now.minute < 5:
                if derniere_verif_resultats != date_du_jour:
                    print(f"Vérification des résultats du {date_du_jour}...")
                    try:
                        from core.results_checker import verifier_resultats_veille
                        from core.canal_manager import publier_bilan_veille
                        bilan = verifier_resultats_veille()
                        if bilan.get('total', 0) > 0:
                            publier_bilan_veille(bot, bilan['texte'])
                    except Exception as e:
                        print(f"⚠️ Erreur vérif résultats : {e}")
                    derniere_verif_resultats = date_du_jour

            # 2. Notifications et Canal (à 8h)
            if now.hour == heure_notif and now.minute < 5:
                if derniere_date_envoi != date_du_jour:
                    print(f"Envoi des notifications du {date_du_jour}...")
                    _envoyer_notifications()
                    derniere_date_envoi = date_du_jour
                    
                    if est_weekend:
                        print("Weekend : envoi des coupons...")
                        _envoyer_coupons_premium()
                        derniere_date_coupons_weekend = date_du_jour
                        
                    if derniere_date_canal != date_du_jour:
                        try:
                            from core.canal_manager import publier_matchs_sur_canal
                            publier_matchs_sur_canal(bot)
                        except Exception as e:
                            print(f"⚠️ Erreur publication canal : {e}")
                        derniere_date_canal = date_du_jour

            # 3. Coupons Semaine (à 10h)
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if derniere_date_coupons_semaine != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    _envoyer_coupons_premium()
                    try:
                        from core.canal_manager import publier_coupons_sur_canal
                        publier_coupons_sur_canal(bot)
                    except Exception as e:
                        print(f"⚠️ Erreur publication coupons canal : {e}")
                    derniere_date_coupons_semaine = date_du_jour

            # 4. Teasing Canal (à 17h)
            if now.hour == 17 and now.minute < 5:
                if derniere_date_teasing != date_du_jour:
                    print(f"Publication du teasing sur le canal...")
                    try:
                        from core.canal_manager import publier_teasing
                        publier_teasing(bot)
                    except Exception as e:
                        print(f"⚠️ Erreur teasing canal : {e}")
                    derniere_date_teasing = date_du_jour

            # 5. Nettoyage automatique (à 3h)
            if now.hour == 3 and now.minute < 5:
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
            print(f"Erreur scheduler globale : {e}")
            time.sleep(60)


threading.Thread(target=_scheduler_notifications, daemon=True).start()


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)

        if update.message:
            user_id = update.message.from_user.id
            
            if est_banni(user_id) and not est_administrateur(user_id):
                return "OK", 200
                
            mode_maintenance = get_parametre("mode_maintenance", "off")
            if mode_maintenance == "on" and not est_administrateur(user_id):
                bot.send_message(user_id, "🛠️ Le bot est actuellement en maintenance. Veuillez réessayer plus tard.")
                return "OK", 200

        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"⚠️ Erreur webhook : {e}")
        return "OK", 200


@app.route('/')
def index():
    return "Bot operationnel !", 200


# =========================================================
# CHARGEMENT INITIAL DU MODÈLE (au démarrage)
# =========================================================
print("🔄 Chargement initial du modèle IA...")
if charger_modele_universel():
    print("✅ Modèle IA chargé avec succès au démarrage !")
else:
    print("⚠️ Impossible de charger le modèle au démarrage. Il sera chargé à la première utilisation.")

initialiser_tables()
print("Bot pret (init differee + notifications + coupons + canal + maintenance).")
