import time
import threading
import telebot

from users import get_langue, est_premium, est_banni
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.top_matches import get_top_affiches, formater_top_affiches
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.utils.logs import log_info, log_error, log_warning


def _envoyer_message_securise(bot, chat_id, texte):
    """Envoie un message en découpant si trop long (Telegram limite à 4096)."""
    limite = 4000
    if len(texte) <= limite:
        bot.send_message(chat_id, texte)
    else:
        morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
        for morceau in morceaux:
            bot.send_message(chat_id, morceau)
            time.sleep(0.4)


def _supprimer_message_silencieux(bot, chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        log_warning(f"Impossible de supprimer le message {message_id} dans {chat_id} : {e}", "PREMIUM")


def _modifier_message_silencieux(bot, chat_id, message_id, texte):
    try:
        bot.edit_message_text(texte, chat_id, message_id)
    except Exception as e:
        log_warning(f"Impossible de modifier le message {message_id} : {e}", "PREMIUM")


def _charger_modele_en_arriere_plan(bot, chat_id, message_id, user_id, langue, action):
    """
    Charge le modèle et exécute l'action demandée en arrière-plan.
    L'utilisateur reçoit un message dès que c'est prêt.
    """
    from core.ml_model import global_model_data, charger_et_entrainer
    
    # 1. On indique à l'utilisateur qu'on charge
    _modifier_message_silencieux(bot, chat_id, message_id, "⏳ Chargement du modèle IA en cours... (cela peut prendre ~30 secondes)")
    
    # 2. On charge le modèle
    try:
        if global_model_data.get('modeles_par_competition') is None:
            success = charger_et_entrainer()
        else:
            success = True
    except Exception as e:
        log_error("Erreur chargement modèle en arrière-plan", "PREMIUM", exception=e)
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Erreur lors du chargement du modèle. Réessaie.")
        return
    
    if not success:
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Impossible de charger le modèle. L'admin a été prévenu.")
        return
    
    # 3. On exécute l'action demandée
    try:
        if action == "matchs_du_jour":
            matchs = get_matchs_du_jour()
            if not matchs:
                _modifier_message_silencieux(bot, chat_id, message_id, "📅 Aucun match disponible ou avec une cote intéressante aujourd'hui.")
                return
            is_prem = est_premium(user_id)
            nb_max = None if is_prem else 15
            texte = formater_matchs_du_jour(matchs, langue, est_premium=is_prem, nb_max=nb_max)
            _supprimer_message_silencieux(bot, chat_id, message_id)
            _envoyer_message_securise(bot, chat_id, texte)
            
        elif action == "coupons":
            data = generer_coupons_du_jour()
            coupons = data['coupons']
            if not coupons:
                _modifier_message_silencieux(bot, chat_id, message_id, "🎟️ Aucun coupon disponible aujourd'hui.")
                return
            is_premium_user = est_premium(user_id)
            _supprimer_message_silencieux(bot, chat_id, message_id)
            if is_premium_user:
                for coupon in coupons:
                    if coupon['cote_totale'] >= 1.30:
                        texte = formater_coupon(coupon, langue, montrer_details=True)
                        _envoyer_message_securise(bot, chat_id, texte)
            else:
                coupon_modere = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
                texte = formater_coupon(coupon_modere, langue, montrer_details=False)
                _envoyer_message_securise(bot, chat_id, texte)
                
        elif action == "top_affiches":
            affiches = get_top_affiches(limite=10)
            if not affiches:
                _modifier_message_silencieux(bot, chat_id, message_id, "🏆 Aucune affiche à fort potentiel aujourd'hui.")
                return
            affiches_filtrees = [a for a in affiches if round(1/a['reco_pct'], 2) >= 1.30]
            if not affiches_filtrees:
                _modifier_message_silencieux(bot, chat_id, message_id, "🏆 Aucune affiche avec une cote intéressante (≥ 1.30) aujourd'hui.")
                return
            is_premium_user = est_premium(user_id)
            _supprimer_message_silencieux(bot, chat_id, message_id)
            if is_premium_user:
                texte = formater_top_affiches(affiches_filtrees, langue, montrer_details=True)
            else:
                texte = formater_top_affiches(affiches_filtrees[:1], langue, montrer_details=False)
            _envoyer_message_securise(bot, chat_id, texte)
            
    except Exception as e:
        log_error(f"Erreur lors de l'exécution de l'action '{action}'", "PREMIUM", exception=e)
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Erreur lors de la génération. L'admin a été prévenu.")


def enregistrer_premium_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📅 Matchs du Jour")
    def handle_matchs_jour(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        log_info(f"Demande de Matchs du Jour par {user_id}", "PREMIUM")

        try:
            if est_banni(user_id):
                bot.reply_to(message, "Tu es banni.")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREMIUM", exception=e)
            return

        # On envoie IMMÉDIATEMENT un message d'attente à Telegram (pour éviter le timeout)
        msg = bot.reply_to(message, "⏳ Chargement du modèle IA en cours...")
        
        # On lance le traitement en arrière-plan
        threading.Thread(
            target=_charger_modele_en_arriere_plan,
            args=(bot, message.chat.id, msg.message_id, user_id, langue, "matchs_du_jour"),
            daemon=True
        ).start()

    @bot.message_handler(func=lambda m: m.text == "🎟️ Coupons")
    def handle_coupons(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        log_info(f"Demande de Coupons par {user_id}", "PREMIUM")

        try:
            if est_banni(user_id):
                bot.reply_to(message, "Tu es banni.")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREMIUM", exception=e)
            return

        msg = bot.reply_to(message, "⏳ Chargement du modèle IA en cours...")
        threading.Thread(
            target=_charger_modele_en_arriere_plan,
            args=(bot, message.chat.id, msg.message_id, user_id, langue, "coupons"),
            daemon=True
        ).start()

    @bot.message_handler(func=lambda m: m.text == "🏆 Top Affiches")
    def handle_top_affiches(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        log_info(f"Demande de Top Affiches par {user_id}", "PREMIUM")

        try:
            if est_banni(user_id):
                bot.reply_to(message, "Tu es banni.")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREMIUM", exception=e)
            return

        msg = bot.reply_to(message, "⏳ Chargement du modèle IA en cours...")
        threading.Thread(
            target=_charger_modele_en_arriere_plan,
            args=(bot, message.chat.id, msg.message_id, user_id, langue, "top_affiches"),
            daemon=True
        ).start()
