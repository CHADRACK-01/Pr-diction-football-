import time
import telebot
from users import get_langue, est_premium, est_banni
from core.paris_builder import generer_coupons_du_jour, formater_coupon
from core.top_matches import get_top_affiches, formater_top_affiches
from core.utils.logs import log_error


def _envoyer_message_securise(bot, chat_id, texte):
    limite = 4000
    try:
        if len(texte) <= limite:
            bot.send_message(chat_id, texte)
        else:
            morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
            for morceau in morceaux:
                bot.send_message(chat_id, morceau)
                time.sleep(0.4)
    except Exception as e:
        log_error(f"Erreur envoi message premium à {chat_id} : {e}", "PREMIUM")


def enregistrer_premium_handlers(bot):

    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Coupons", "Coupons du jour", "Coupons ya lelo"
    ])
    def handle_coupons(message):
        print(f"[PREMIUM] Bouton Coupons cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        bot.reply_to(message, "Construction des coupons en cours...")

        try:
            data = generer_coupons_du_jour()
            coupons = data['coupons']

            if not coupons:
                bot.send_message(message.chat.id, "Aucun coupon disponible aujourd'hui.")
                return

            is_premium = est_premium(user_id)

            if is_premium:
                for coupon in coupons:
                    if coupon['cote_totale'] >= 1.30:
                        texte = formater_coupon(coupon, langue, montrer_details=True)
                        _envoyer_message_securise(bot, message.chat.id, texte)
            else:
                coupon_modere = next((c for c in coupons if c['niveau'] == 'modere'), coupons[0])
                texte = formater_coupon(coupon_modere, langue, montrer_details=False)
                _envoyer_message_securise(bot, message.chat.id, texte)

        except Exception as e:
            log_error(f"ERREUR COUPONS : {e}", "PREMIUM")
            bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")


    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Top affiches", "Affiches du jour", "Affiches ya lelo"
    ])
    def handle_top_affiches(message):
        print(f"[PREMIUM] Bouton Top affiches cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        bot.reply_to(message, "Recherche des meilleures affiches...")

        try:
            affiches = get_top_affiches(limite=10)

            if not affiches:
                bot.send_message(message.chat.id, "Aucune affiche à fort potentiel aujourd'hui.")
                return

            affiches_filtrees = [a for a in affiches if round(1/a['reco_pct'], 2) >= 1.30]

            if not affiches_filtrees:
                bot.send_message(message.chat.id, "Aucune affiche avec une cote intéressante (≥ 1.30) aujourd'hui.")
                return

            is_premium = est_premium(user_id)

            if is_premium:
                texte = formater_top_affiches(affiches_filtrees, langue, montrer_details=True)
                _envoyer_message_securise(bot, message.chat.id, texte)
            else:
                texte = formater_top_affiches(affiches_filtrees[:1], langue, montrer_details=False)
                _envoyer_message_securise(bot, message.chat.id, texte)

        except Exception as e:
            log_error(f"ERREUR TOP AFFICHES : {e}", "PREMIUM")
            bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")


    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Matchs du jour", "Today's matches", "Masano ya lelo"
    ])
    def handle_matchs_jour(message):
        print(f"[PREMIUM] Bouton Matchs du jour cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni.")
            return

        bot.reply_to(message, "Recherche des matchs du jour...")

        try:
            from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
            matchs = get_matchs_du_jour()
            is_prem = est_premium(user_id)
            nb_max = None if is_prem else 15

            texte = formater_matchs_du_jour(matchs, langue, est_premium=is_prem, nb_max=nb_max)
            
            limite = 4000
            if len(texte) <= limite:
                bot.send_message(message.chat.id, texte)
            else:
                morceaux = [texte[i:i+limite] for i in range(0, len(texte), limite)]
                for morceau in morceaux:
                    bot.send_message(message.chat.id, morceau)
                    time.sleep(0.5)
                    
        except Exception as e:
            log_error(f"ERREUR MATCHS DU JOUR : {e}", "PREMIUM")
            bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")
