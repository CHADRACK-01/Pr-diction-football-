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

from config import TOKEN, MODE_VITRINE, TURSO_URL, TURSO_TOKEN
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
    """Charge les modèles depuis Turso (table models_cache)."""
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
        
    texte += "Tape une affiche pour plus de détails.\nPour désactiver : /notif_off"

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

    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT user_id FROM utilisateurs
            WHERE status = 'premium'
            AND (date_expiration IS NULL OR date_expiration > datetime('now'))
        """)
        premiums = [row[0] for row in cur.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Erreur lecture premiums : {e}")
        return

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
    """Tâche de fond qui gère les envois automatiques."""
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

            try:
                heure_notif_val = get_parametre("notif_heure", "8")
            except Exception:
                heure_notif_val = "8"

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
                    try:
                        from core.results_checker import verifier_resultats_veille
                        from core.canal_manager import publier_bilan_veille
                        bilan = verifier_resultats_veille()
                        if bilan.get('total', 0) > 0:
                            publier_bilan_veille(bot, bilan['texte'])
                    except Exception as e:
                        print(f"Erreur vérif résultats : {e}")
                    derniere_verif_resultats = date_du_jour

            # 2. Notifications et Canal (à 8h)
            if now.hour == heure_notif and now.minute < 5:
                if derniere_date_envoi != date_du_jour:
                    print(f"Envoi des notifications du {date_du_jour}...")
                    try:
                        _envoyer_notifications()
                    except Exception as e:
                        print(f"Erreur notifs : {e}")
                    derniere_date_envoi = date_du_jour
                    
                    if est_weekend:
                        print("Weekend : envoi des coupons...")
                        try:
                            _envoyer_coupons_premium()
                        except Exception as e:
                            print(f"Erreur coupons : {e}")
                        derniere_date_coupons_weekend = date_du_jour
                        
                    if derniere_date_canal != date_du_jour:
                        try:
                            from core.canal_manager import publier_matchs_sur_canal
                            publier_matchs_sur_canal(bot)
                        except Exception as e:
                            print(f"Erreur canal : {e}")
                        derniere_date_canal = date_du_jour

            # 3. Coupons Semaine (à 10h)
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if derniere_date_coupons_semaine != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    try:
                        _envoyer_coupons_premium()
                        from core.canal_manager import publier_coupons_sur_canal
                        publier_coupons_sur_canal(bot)
                    except Exception as e:
                        print(f"Erreur coupons : {e}")
                    derniere_date_coupons_semaine = date_du_jour

            # 4. Teasing Canal (à 17h)
            if now.hour == 17 and now.minute < 5:
                if derniere_date_teasing != date_du_jour:
                    print(f"Publication du teasing sur le canal...")
                    try:
                        from core.canal_manager import publier_teasing
                        publier_teasing(bot)
                    except Exception as e:
                        print(f"Erreur teasing : {e}")
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


def _lancer_scheduler_apres_delai():
    """Lance le scheduler après un délai pour laisser la BDD s'initialiser."""
    time.sleep(60)
    _scheduler_notifications()


# =========================================================
# ROUTES FLASK
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Point d'entrée pour les mises à jour Telegram."""
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)

    if update.message:
        user_id = update.message.from_user.id
        
        try:
            is_banned = est_banni(user_id)
            is_admin = est_administrateur(user_id)
        except Exception:
            is_banned = False
            is_admin = False
        
        if is_banned and not is_admin:
            return "OK", 200
            
        try:
            mode_maintenance = get_parametre("mode_maintenance", "off")
        except Exception:
            mode_maintenance = "off"
            
        if mode_maintenance == "on" and not is_admin:
            try:
                bot.send_message(user_id, "🛠️ Le bot est actuellement en maintenance. Veuillez réessayer plus tard.")
            except Exception:
                pass
            return "OK", 200

    try:
        bot.process_new_updates([update])
    except Exception as e:
        print(f"❌ Erreur traitement update : {e}")
        import traceback
        traceback.print_exc()
    
    return "OK", 200


@app.route('/')
def index():
    """Route de santé pour Render/UptimeRobot."""
    return "Bot operationnel !", 200


@app.route('/init_db')
def init_db():
    """Route de debug pour créer les tables manuellement."""
    from users.db import initialiser_tables, get_connection
    try:
        initialiser_tables()
        
        # Vérification
        conn = get_connection()
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        noms = [r[0] for r in result]
        conn.close()
        
        return f"✅ Tables créées !\n\nTables existantes :\n{chr(10).join(noms)}", 200
    except Exception as e:
        import traceback
        return f"❌ Erreur : {e}\n\n{traceback.format_exc()}", 500


@app.route('/health')
def health():
    """Route de santé avancée : vérifie la connexion Turso."""
    from users.db import get_connection
    try:
        conn = get_connection()
        result = conn.execute("SELECT 1").fetchone()
        conn.close()
        
        if result and result[0] == 1:
            return "✅ Turso OK", 200
        else:
            return "❌ Turso ne répond pas", 500
    except Exception as e:
        return f"❌ Turso erreur : {e}", 500


@app.route('/debug_env')
def debug_env():
    """Route de debug pour vérifier les variables d'environnement."""
    url_ok = "✅" if TURSO_URL else "❌"
    token_ok = "✅" if TURSO_TOKEN else "❌"
    token_ok_short = "✅" if TOKEN else "❌"
    
    return f"""
    Variables d'environnement :
    
    TURSO_URL : {url_ok} (longueur={len(TURSO_URL)})
    TURSO_TOKEN : {token_ok} (longueur={len(TURSO_TOKEN)})
    TELEGRAM_TOKEN : {token_ok_short} (longueur={len(TOKEN)})
    MODE_VITRINE : {MODE_VITRINE}
    """, 200
    @app.route('/webhook_info')
def webhook_info():
    """Affiche les informations du webhook actuel (messages en attente)."""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if not data.get('ok'):
            return f"❌ Erreur API Telegram : {data}", 500
        
        info = data.get('result', {})
        
        texte = "📡 **INFORMATIONS DU WEBHOOK**\n\n"
        texte += f"🔗 URL : {info.get('url', '❌ Non définie')}\n"
        texte += f"📥 Messages en attente : {info.get('pending_update_count', 0)}\n"
        texte += f"🔧 Dernière erreur : {info.get('last_error_message', 'Aucune')}\n"
        texte += f"📅 Date dernière erreur : {info.get('last_error_date', 'N/A')}\n"
        texte += f"✅ Certificat : {info.get('has_custom_certificate', False)}\n"
        
        # Les mises à jour autorisées
        allowed = info.get('allowed_updates', [])
        if allowed:
            texte += f"\n📋 Mises à jour autorisées :\n"
            for u in allowed:
                texte += f"   • {u}\n"
        else:
            texte += f"\n📋 Mises à jour autorisées : Toutes\n"
        
        # Les dernières erreurs (10 max)
        if info.get('last_error_message'):
            texte += f"\n⚠️ **Dernière erreur :**\n{info['last_error_message']}\n"
        
        return texte, 200
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/delete_webhook')
def delete_webhook():
    """Supprime le webhook actuel."""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=false"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get('ok'):
            return "✅ Webhook supprimé avec succès !\n\nLe bot ne recevra plus les messages via webhook.\n⚠️ Pour le redéfinir, redéploie sur Render ou envoie /set_webhook", 200
        else:
            return f"❌ Erreur : {data}", 500
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/delete_webhook_pending')
def delete_webhook_pending():
    """Supprime le webhook ET les messages en attente."""
    import requests
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get('ok'):
            return "✅ Webhook supprimé ET messages en attente supprimés !", 200
        else:
            return f"❌ Erreur : {data}", 500
    except Exception as e:
        return f"❌ Erreur : {e}", 500


@app.route('/set_webhook')
def set_webhook():
    """Redéfinit le webhook avec l'URL actuelle de Render."""
    import requests
    try:
        # Détection automatique de l'URL (fonctionne sur Render)
        host = request.headers.get('Host', 'prediction-football-209y.onrender.com')
        webhook_url = f"https://{host}/{TOKEN}"
        
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get('ok'):
            return f"✅ Webhook défini :\n{webhook_url}\n\n📥 Les nouveaux messages arriveront ici.", 200
        else:
            return f"❌ Erreur : {data}", 500
    except Exception as e:
        return f"❌ Erreur : {e}", 500


# =========================================================
# INITIALISATION AU DÉMARRAGE
# =========================================================
print("🔄 Initialisation de la base de données...")
try:
    initialiser_tables()
    print("✅ Initialisation terminée.")
except Exception as e:
    print(f"❌ Erreur initialisation : {e}")

# ⚠️ Le scheduler démarre APRÈS un délai de 60s
if not MODE_VITRINE:
    threading.Thread(target=_lancer_scheduler_apres_delai, daemon=True).start()
    print("✅ Scheduler programmé (démarrage dans 60s).")
else:
    print("⚠️ Mode vitrine : scheduler désactivé.")

print("✅ Bot prêt.")
