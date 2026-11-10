import time
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
    """Supprime un message (sans crasher si déjà supprimé)."""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        log_warning(f"Impossible de supprimer le message {message_id} dans {chat_id} : {e}", "PREMIUM")


def _modifier_message_silencieux(bot, chat_id, message_id, texte):
    """Modifie un message (sans crasher si déjà supprimé ou modifié)."""
    try:
        bot.edit_message_text(texte, chat_id, message_id)
    except Exception as e:
        log_warning(f"Impossible de modifier le message {message_id} : {e}", "PREMIUM")


def enregistrer_premium_handlers(bot):

    # =========================================================
    # MATCHS DU JOUR (📅 Matchs du Jour)
    # =========================================================
    @bot.message_handler(func=lambda m: m.text == "📅 Matchs du Jour")
    def handle_matchs_jour(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        log_info(f"Demande de Matchs du Jour par {user_id}", "PREMIUM")

        # Vérification banni
        try:
            if est_banni(user_id):
                bot.reply_to(message, "Tu es banni.")
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREMIUM", exception=e)
            return

        msg = bot.reply_to(message, "🔍 Recherche des matchs du jour en cours...")

        try:
            matchs = get_matchs_du_jour()
        except Exception as e:
            log_error("Erreur lors de la récupération des matchs du jour", "PREMIUM", exception=e)
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "❌ Une erreur est survenue lors de la récupération des matchs. L'admin a été prévenu.")
            return

        if not matchs:
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "📅 Aucun match disponible ou avec une cote intéressante aujourd'hui.")
            return

        try:
            is_prem = est_premium(user_id)
            nb_max = None if is_prem else 15
            texte = formater_matchs_du_jour(matchs, langue, est_premium=is_prem, nb_max=nb_max)
        except Exception as e:
            log_error("Erreur lors du formatage des matchs du jour", "PREMIUM", exception=e)
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "❌ Erreur lors du formatage des matchs.")
            return

        _supprimer_message_silencieux(bot, message.chat.id, msg.message_id)
        _envoyer_message_securise(bot, message.chat.id, texte)

    # =========================================================
    # COUPONS (🎟️ Coupons)
    # =========================================================
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

        msg = bot.reply_to(message, "🎟️ Construction des coupons en cours...")

        try:
            data = generer_coupons_du_jour()
            coupons = data['coupons']
        except Exception as e:
            log_error("Erreur lors de la génération des coupons", "PREMIUM", exception=e)
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "❌ Une erreur est survenue lors de la génération des coupons. L'admin a été prévenu.")
            return

        if not coupons:
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "🎟️ Aucun coupon disponible aujourd'hui.")
            return

        try:
            is_premium_user = est_premium(user_id)
        except Exception as e:
            log_error(f"Impossible de vérifier le statut premium de {user_id}", "PREMIUM", exception=e)
            is_premium_user = False

        _supprimer_message_silencieux(bot, message.chat.id, msg.message_id)

        try:
            if is_premium_user:
                for coupon in coupons:
                    if coupon['cote_totale'] >= 1.30:
                        texte = formater_coupon(coupon, langue, montrer_details=True)
                        _envoyer_message_securise(bot, message.chat.id, texte)
            else:
                coupon_modere = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
                texte = formater_coupon(coupon_modere, langue, montrer_details=False)
                _envoyer_message_securise(bot, message.chat.id, texte)
        except Exception as e:
            log_error(f"Erreur lors de l'envoi des coupons à {user_id}", "PREMIUM", exception=e)

    # =========================================================
    # TOP AFFICHES (🏆 Top Affiches)
    # =========================================================
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

        msg = bot.reply_to(message, "🔍 Recherche des meilleures affiches...")

        try:
            affiches = get_top_affiches(limite=10)
        except Exception as e:
            log_error("Erreur lors de la recherche des top affiches", "PREMIUM", exception=e)
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "❌ Une erreur est survenue lors de la recherche des top affiches. L'admin a été prévenu.")
            return

        if not affiches:
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "🏆 Aucune affiche à fort potentiel aujourd'hui.")
            return

        affiches_filtrees = [a for a in affiches if round(1/a['reco_pct'], 2) >= 1.30]

        if not affiches_filtrees:
            _modifier_message_silencieux(bot, message.chat.id, msg.message_id, 
                                          "🏆 Aucune affiche avec une cote intéressante (≥ 1.30) aujourd'hui.")
            return

        try:
            is_premium_user = est_premium(user_id)
        except Exception as e:
            log_error(f"Impossible de vérifier le statut premium de {user_id}", "PREMIUM", exception=e)
            is_premium_user = False

        _supprimer_message_silencieux(bot, message.chat.id, msg.message_id)

        try:
            if is_premium_user:
                texte = formater_top_affiches(affiches_filtrees, langue, montrer_details=True)
            else:
                texte = formater_top_affiches(affiches_filtrees[:1], langue, montrer_details=False)
            _envoyer_message_securise(bot, message.chat.id, texte)
        except Exception as e:
            log_error(f"Erreur lors de l'envoi des top affiches à {user_id}", "PREMIUM", exception=e)
