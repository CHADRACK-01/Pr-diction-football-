import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

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
from telegram_bot.admin_handlers import enregistrer_admin_handlers
from telegram_bot.inline_handlers import enregistrer_inline_handlers

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ⚠️ ORDRE CRUCIAL D'ENREGISTREMENT DES HANDLERS
enregistrer_admin_handlers(bot)
enregistrer_inline_handlers(bot)
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))


# =========================================================
# NOTIFICATIONS QUOTIDIENNES (FILTRÉES)
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

        # On demande plus de pronostics pour pouvoir filtrer
        top = get_top_pronostics_du_jour(nb=15)

        if not top:
            print("Notifications : aucun pronostic disponible")
            return

        date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
        texte = f"🔥 **PRONOSTICS VALUE BET DU JOUR** 🔥\nDate : {date_str}\n\n"
        
        compte = 0
        for item in top:
            prono = item['prono']
            
            # Utilisation de la nouvelle analyse
            analyse = prono.get('analyse_pari')
            if not analyse:
                continue
                
            # FILTRE : On ne garde que si Cote > 1.25 ET Confiance > 65%
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
                        texte += f"🔥 **VALUE BET !**\n"
                
                texte += f"⚽ Score probable : {prono['best_score'][0]} - {prono['best_score'][1]}\n\n"
            
            if compte >= 3: # On s'arrête à 3 top pronostics
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
                bot.send_message(uid, texte, parse_mode='Markdown')
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
# SCHEDULER (Le Cerveau du Bot)
# =========================================================
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

            # Lecture dynamique de l'heure des notifs (depuis la BDD)
            try:
                heure_notif = int(get_parametre("notif_heure", 8))
            except:
                heure_notif = 8

            # 1. Vérification des résultats de la veille et publication du Bilan (à 7h)
            if now.hour == 7 and now.minute < 5:
                if derniere_verif_resultats != date_du_jour:
                    print(f"Vérification des résultats du {date_du_jour}...")
                    from core.results_checker import verifier_resultats_veille
                    from core.canal_manager import publier_bilan_veille
                    
                    bilan = verifier_resultats_veille()
                    if bilan['total'] > 0:
                        publier_bilan_veille(bot, bilan['texte'])
                    
                    derniere_verif_resultats = date_du_jour

            # 2. Notifications aux utilisateurs et Publication Matchs sur Canal (à 8h)
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
                        from core.canal_manager import publier_matchs_sur_canal
                        publier_matchs_sur_canal(bot)
                        derniere_date_canal = date_du_jour

            # 3. Coupons Semaine (à 10h)
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if derniere_date_coupons_semaine != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    _envoyer_coupons_premium()
                    derniere_date_coupons_semaine = date_du_jour

            # 4. Teasing Canal (à 17h)
            if now.hour == 17 and now.minute < 5:
                if derniere_date_teasing != date_du_jour:
                    print(f"Publication du teasing sur le canal...")
                    from core.canal_manager import publier_teasing
                    publier_teasing(bot)
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
            print(f"Erreur scheduler : {e}")
            time.sleep(60)


threading.Thread(target=_scheduler_notifications, daemon=True).start()


# =========================================================
# WEBHOOK (Gestion des requêtes Telegram)
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
print("Bot pret (init differee + notifications + coupons + canal + maintenance).")
