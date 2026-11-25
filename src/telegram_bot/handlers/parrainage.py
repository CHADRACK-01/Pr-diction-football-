import telebot
from users import (
    get_langue, get_user_info, compter_filleuls,
    get_top_parrains, get_filleuls, get_palier_atteint, get_prochain_palier
)
from core.utils.logs import log_info, log_error, log_warning
from core.utils.markdown import formater_proprement

BOT_USERNAME = "MonPronosticFootball_bot"


def enregistrer_parrainage_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "🤝 Parrainage")
    def handle_parrainage(message):
        user_id = message.from_user.id
        log_info(f"Menu parrainage demandé par {user_id}", "PARRAINAGE")

        try:
            langue = get_langue(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la langue de {user_id}", "PARRAINAGE", exception=e)
            langue = "fr"

        try:
            code = f"REF{user_id}"
            lien = f"https://t.me/{BOT_USERNAME}?start={code}"
        except Exception as e:
            log_error(f"Impossible de générer le lien de parrainage pour {user_id}", "PARRAINAGE", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la génération de ton lien. Réessaie.")
            return

        try:
            nb_filleuls = compter_filleuls(user_id)
        except Exception as e:
            log_error(f"Impossible de compter les filleuls de {user_id}", "PARRAINAGE", exception=e)
            nb_filleuls = 0

        texte = (
            f"🤝 **PARRAINAGE**\n\n"
            f"Invite tes amis et gagne des jours Premium gratuits !\n\n"
            f"🎁 **Gains** :\n"
            f"• 1 ami inscrit = 1 jour Premium pour toi ET ton ami\n"
            f"• 5 amis inscrits = 7 jours Premium bonus\n\n"
            f"🔗 **Ton lien** :\n{lien}\n\n"
            f"📊 **Tes stats** :\n"
            f"• Filleuls : {nb_filleuls}\n"
            f"• Ton code : {code}"
        )

        try:
            palier = get_palier_atteint(nb_filleuls)
            if palier:
                texte += f"\n\n🏆 Palier atteint : **{palier['nom']}** (bonus +{palier['bonus']}j)"
        except Exception as e:
            log_warning(f"Impossible de calculer le palier pour {user_id} : {e}", "PARRAINAGE")

        try:
            prochain = get_prochain_palier(nb_filleuls)
            if prochain:
                texte += f"\n🎯 Prochain palier : **{prochain['nom']}** dans {prochain['restant']} filleul(s) (+{prochain['bonus']}j bonus)"
        except Exception as e:
            log_warning(f"Impossible de calculer le prochain palier pour {user_id} : {e}", "PARRAINAGE")

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("🏆 Classement", callback_data="parr|classement"),
            telebot.types.InlineKeyboardButton("👥 Mes filleuls", callback_data="parr|filleuls")
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "📤 Partager",
                url=f"https://t.me/share/url?url={lien}&text=Rejoins ce bot de pronostics !"
            )
        )
        
        try:
            # ⚠️ Échappement du Markdown pour éviter les erreurs
            texte_secu = formater_proprement(texte)
            bot.reply_to(message, texte_secu, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            log_error(f"Impossible d'envoyer le menu parrainage à {user_id} (Markdown)", "PARRAINAGE", exception=e)
            # Fallback sans Markdown
            try:
                bot.reply_to(message, texte.replace("**", ""), reply_markup=markup)
            except Exception as e2:
                log_error(f"Impossible d'envoyer le menu parrainage à {user_id} (fallback)", "PARRAINAGE", exception=e2)

    @bot.callback_query_handler(func=lambda call: call.data == "parr|classement")
    def parrainage_classement(call):
        user_id = call.from_user.id
        
        try:
            top = get_top_parrains(limite=10)
        except Exception as e:
            log_error(f"Impossible de récupérer le classement des parrains", "PARRAINAGE", exception=e)
            try:
                bot.answer_callback_query(call.id, "❌ Erreur")
                bot.send_message(call.message.chat.id, "❌ Impossible de charger le classement. L'admin a été prévenu.")
            except Exception:
                pass
            return

        if not top:
            try:
                bot.answer_callback_query(call.id, "Aucun parrain")
                bot.send_message(call.message.chat.id, "🏆 **CLASSEMENT DES PARRAINS**\n\nAucun parrain pour l'instant. Sois le premier !", parse_mode="Markdown")
            except Exception as e:
                log_warning(f"Impossible d'envoyer le message classement à {user_id} : {e}", "PARRAINAGE")
            return

        texte = "🏆 **CLASSEMENT DES PARRAINS**\n\n"
        for i, p in enumerate(top, 1):
            nom = p.get('first_name') or 'Anonyme'
            nb = p.get('nb_filleuls', 0)
            texte += f"{i}. {nom} - {nb} filleul(s)\n"
        
        try:
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
        except Exception as e:
            log_error(f"Impossible d'envoyer le classement à {user_id}", "PARRAINAGE", exception=e)

    @bot.callback_query_handler(func=lambda call: call.data == "parr|filleuls")
    def parrainage_mes_filleuls(call):
        user_id = call.from_user.id
        
        try:
            filleuls = get_filleuls(user_id, limite=20)
        except Exception as e:
            log_error(f"Impossible de récupérer les filleuls de {user_id}", "PARRAINAGE", exception=e)
            try:
                bot.answer_callback_query(call.id, "❌ Erreur")
                bot.send_message(call.message.chat.id, "❌ Impossible de charger tes filleuls. L'admin a été prévenu.")
            except Exception:
                pass
            return

        if not filleuls:
            try:
                bot.answer_callback_query(call.id, "Aucun filleul")
                bot.send_message(call.message.chat.id, "👥 **MES FILLEULS**\n\nTu n'as pas encore de filleul.", parse_mode="Markdown")
            except Exception as e:
                log_warning(f"Impossible d'envoyer le message filleuls à {user_id} : {e}", "PARRAINAGE")
            return

        texte = f"👥 **MES FILLEULS ({len(filleuls)})**\n\n"
        for i, f in enumerate(filleuls, 1):
            nom = f.get('first_name') or 'Anonyme'
            date_inscr = f.get('date_inscription')
            if date_inscr:
                try:
                    date_str = str(date_inscr).split(" ")[0]
                    parts = date_str.split("-")
                    if len(parts) == 3:
                        date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
                except Exception:
                    date_str = "?"
            else:
                date_str = "?"
            texte += f"{i}. {nom} - {date_str}\n"
        
        try:
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
        except Exception as e:
            log_error(f"Impossible d'envoyer les filleuls à {user_id}", "PARRAINAGE", exception=e)
