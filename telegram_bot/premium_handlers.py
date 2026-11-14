# telegram_bot/premium_handlers.py
import time
import threading
import telebot

from users import get_langue, est_premium, est_banni
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.top_matches import get_top_affiches, formater_top_affiches
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.utils.logs import log_info, log_error, log_warning


def _envoyer_message_securise(bot, chat_id, texte):
    """Envoie un message en HTML (gère la limite de 4096 caractères)."""
    limite = 4000
    if len(texte) <= limite:
        try:
            # ⚠️ C'EST ICI QUE TOUT SE JOUE : parse_mode="HTML"
            bot.send_message(chat_id, texte, parse_mode="HTML")
        except Exception as e:
            log_warning(f"Erreur HTML, envoi en texte brut : {e}", "PREMIUM")
            try:
                bot.send_message(chat_id, texte)
            except Exception as e2:
                log_error(f"Impossible d'envoyer le message : {e2}", "PREMIUM")
    else:
        morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
        for morceau in morceaux:
            try:
                bot.send_message(chat_id, morceau, parse_mode="HTML")
            except Exception:
                try:
                    bot.send_message(chat_id, morceau)
                except Exception:
                    pass
            time.sleep(0.4)


def _supprimer_message_silencieux(bot, chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        log_warning(f"Impossible de supprimer le message {message_id} : {e}", "PREMIUM")


def _modifier_message_silencieux(bot, chat_id, message_id, texte):
    try:
        bot.edit_message_text(texte, chat_id, message_id, parse_mode="HTML")
    except Exception as e:
        msg_err = str(e).lower()
        if "message is not modified" in msg_err:
            return
        log_warning(f"Impossible de modifier le message {message_id} : {e}", "PREMIUM")


def _charger_modele_en_arriere_plan(bot, chat_id, message_id, user_id, langue, action):
    from core.ml_model import global_model_data, charger_et_entrainer
    
    _modifier_message_silencieux(bot, chat_id, message_id, "⏳ Chargement du modèle IA en cours...")
    
    try:
        if global_model_data.get('models') is None:
            success = charger_et_entrainer()
        else:
            success = True
    except Exception as e:
        log_error("Erreur chargement modèle", "PREMIUM", exception=e)
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Erreur lors du chargement du modèle.")
        return
    
    if not success:
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Impossible de charger le modèle.")
        return
    
    try:
        # --- MATCHS DU JOUR ---
        if action == "matchs_du_jour":
            matchs = get_matchs_du_jour()
            if not matchs:
                _modifier_message_silencieux(bot, chat_id, message_id, "📅 Aucun match disponible aujourd'hui.")
                return
            is_prem = est_premium(user_id)
            nb_max = None if is_prem else 50
            texte = formater_matchs_du_jour(matchs, langue, est_premium=is_prem, nb_max=nb_max)
            _supprimer_message_silencieux(bot, chat_id, message_id)
            _envoyer_message_securise(bot, chat_id, texte)
            
        # --- COUPONS ---
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
                
        # --- TOP AFFICHES ---
        elif action == "top_affiches":
            affiches = get_top_affiches(limite=10)
            if not affiches:
                _modifier_message_silencieux(bot, chat_id, message_id, "🏆 Aucune affiche à fort potentiel aujourd'hui.")
                return
            affiches_filtrees = [a for a in affiches if round(1/a['reco_pct'], 2) >= 1.30]
            if not affiches_filtrees:
                _modifier_message_silencieux(bot, chat_id, message_id, "🏆 Aucune affiche avec une cote intéressante aujourd'hui.")
                return
            is_premium_user = est_premium(user_id)
            _supprimer_message_silencieux(bot, chat_id, message_id)
            if is_premium_user:
                texte = formater_top_affiches(affiches_filtrees, langue, montrer_details=True)
            else:
                texte = formater_top_affiches(affiches_filtrees[:1], langue, montrer_details=False)
            _envoyer_message_securise(bot, chat_id, texte)
            
    except Exception as e:
        log_error(f"Erreur action '{action}'", "PREMIUM", exception=e)
        _modifier_message_silencieux(bot, chat_id, message_id, "❌ Erreur lors de la génération.")


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
        except Exception:
            return

        msg = bot.reply_to(message, "⏳ Chargement du modèle IA en cours...")
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
        except Exception:
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
        except Exception:
            return

        msg = bot.reply_to(message, "⏳ Chargement du modèle IA en cours...")
        threading.Thread(
            target=_charger_modele_en_arriere_plan,
            args=(bot, message.chat.id, msg.message_id, user_id, langue, "top_affiches"),
            daemon=True
        ).start()
