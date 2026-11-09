import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import time
import threading
import telebot
from datetime import datetime, timezone, timedelta
from flask import Flask, request

# =========================================================
# ⚠️ SÉCURITÉ GLOBALE : Activation AVANT tout le reste
# =========================================================
from core.utils.error_handler import activer_capture_globale
activer_capture_globale()

from config import TOKEN, MODE_VITRINE
from users import (
    initialiser_tables, get_utilisateurs_notifies, est_banni, 
    est_administrateur, get_parametre
)
from telegram_bot.handlers import enregistrer_handlers

# Initialisation du bot et de l'application Flask
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Enregistrement de tous les handlers
enregistrer_handlers(bot)

TZ_KINSHASA = timezone(timedelta(hours=1))


def _envoyer_message_securise(chat_id, texte, parse_mode=None):
    """Envoie un message en gérant la limite de 4096 caractères de Telegram."""
    limite = 4000
    if len(texte) <= limite:
        bot.send_message(chat_id, texte, parse_mode=parse_mode)
    else:
        morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
        for morceau in morceaux:
            bot.send_message(chat_id, morceau, parse_mode=parse_mode)
            time.sleep(0.3)


def charger_modele_universel():
    """
    Charge les modèles depuis Turso (table models_cache).
    """
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
    """Envoie les meilleurs pronostics du jour aux utilisateurs abonnés."""
    if not charger_modele_universel():
        print("Notifications : impossible de charger le modèle.")
        return

    from core.daily_matches import get_matchs_du_jour
    
    matchs = get_matchs_du_jour()
    if not matchs:
        print("Notifications : aucun match disponible.")
        return

    # On prend les 3 meilleurs matchs par confiance DC
    top_3 = sorted(matchs, key=lambda x: x['dc_pct'], reverse=True)[:3]
    
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    texte = f"🔥 **TOP 3 PRONOSTICS DU JOUR** 🔥\nDate : {date_str}\n\n"
    
    for i, m in enumerate(top_3, 1):
        texte += (
            f"{i}. **{m['home']} vs {m['away']}**\n"
            f"   🛡️ DC : {m['dc_label']} ({round(m['dc_pct']*100, 1)}%)\n"
            f"   🎯 BTTS : {round(m['btts']*100, 1)}% | 🥅 Over 2.5 : {round(m['over_25']*100, 1)}%\n"
        )
        analyse = m.get('analyse_pari')
        if analyse and analyse.get('cote_book'):
            texte += f"   🏢 Cote Book : {analyse['cote_book']}\n"
            if analyse.get('is_value'):
                texte += f"   🔥 VALUE BET !\n"
        texte += "\n"
        
    texte += (
        "Tape une affiche pour plus de détails.\n"
        "Pour désactiver : /notif_off"
    )

    users = get_utilisateurs_notifies()
    succes = 0
    echecs = 0
    for uid in users:
        try:
            _envoyer_message_securise(uid, texte, parse_mode='Markdown')
            succes += 1
            time.sleep(0.1)
        except Exception:
            echecs += 1

    print(f"Notifications envoyées : {succes} succès, {echecs} échecs")


def _envoyer_coupons_premium():
    """Génère et envoie les coupons du jour uniquement aux utilisateurs Premium."""
    if not charger_modele_universel():
        print("Coupons : impossible de charger le modèle.")
        return

    from core.paris_builder import generer_coupons_du_jour, formater_coupon
    from users import get_langue
    from users.db import get_connection

    data = generer_coupons_du_jour()
    coupons = data['coupons']
    if not coupons:
        print("Aucun coupon à envoyer.")
        return

    conn = get_connection()
    cur = conn.execute("""
        SELECT user_id FROM utilisateurs
        WHERE status = 'premium'
        AND (date_expiration IS NULL OR date_expiration > datetime('now'))
    """)
    premiums = [row[0] for row in cur.fetchall()]
    conn.close()

    succes = 0
    for uid in premiums:
        langue = get_langue(uid)
        for coupon in coupons:
            texte = formater_coupon(coupon, langue, montrer_details=True)
            _envoyer_message_securise(uid, texte)
            time.sleep(0.1)
        succes += 1

    print(f"📤 Coupons envoyés à {succes} Premium(s)")


def _scheduler_notifications():
    """Tâche de fond qui gère les envois automatiques (notifications, canal, nettoyage)."""
    print("Scheduler démarré...")
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

            heure_notif_val = get_parametre("notif_heure", "8")
            if isinstance(heure_notif_val, str) and heure_notif_val.isdigit():
                heure_notif = int(heure_notif_val)
            elif isinstance(heure_notif_val, int):
                heure_notif = heure_notif_val
            else:
                heure_notif = 8

            # 1. Vérification des résultats de la veille (à 7h)
            if now.hour == 7 and now.minute < 5:
                if derniere_verif_resultats != date_du_jour:
                    print(f"Vérification des résultats du {date_du_jour}...")
                    from core.results_checker import verifier_resultats_veille
                    from core.canal_manager import publier_bilan_veille
                    bilan = verifier_resultats_veille()
                    if bilan.get('total', 0) > 0:
                        publier_bilan_veille(bot, bilan['texte'])
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
                        from core.canal_manager import publier_matchs_sur_canal
                        publier_matchs_sur_canal(bot)
                        derniere_date_canal = date_du_jour

            # 3. Coupons Semaine (à 10h)
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if derniere_date_coupons_semaine != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    _envoyer_coupons_premium()
                    from core.canal_manager import publier_coupons_sur_canal
                    publier_coupons_sur_canal(bot)
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
                    from users import nettoyer_logs_anciens, nettoyer_paiements_anciens
                    nettoyer_logs_anciens(jours=30)
                    nettoyer_paiements_anciens(jours=90)
                    dernier_nettoyage = date_du_jour

            time.sleep(60)
        except Exception as e:
            print(f"Erreur scheduler globale : {e}")
            time.sleep(60)


def _lancer_scheduler_apres_delai():
    """Lance le scheduler après un délai pour laisser la BDD s'initialiser."""
    time.sleep(30)  # On attend 30 secondes que la BDD soit prête
    _scheduler_notifications()


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Point d'entrée pour les mises à jour Telegram."""
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


@app.route('/')
def index():
    """Route de santé pour Render/UptimeRobot."""
    return "Bot operationnel !", 200


# =========================================================
# INITIALISATION AU DÉMARRAGE
# =========================================================
print("🔄 Initialisation de la base de données...")
initialiser_tables()
print("✅ Tables prêtes.")

# ⚠️ Le scheduler démarre APRÈS un délai de 30s (via le thread)
if not MODE_VITRINE:
    threading.Thread(target=_lancer_scheduler_apres_delai, daemon=True).start()
    print("✅ Scheduler programmé (démarrage dans 30s).")
else:
    print("⚠️ Mode vitrine : scheduler désactivé.")

print("✅ Bot prêt.")
