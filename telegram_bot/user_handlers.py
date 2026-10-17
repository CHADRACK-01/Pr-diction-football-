import telebot
import pandas as pd

from config import FICHIER_HISTORIQUE
from users import (
    get_langue, set_langue, est_banni, est_premium,
    peut_faire_pronostic, get_limite_jour,
    activer_notifications, desactiver_notifications,
    compter_filleuls, get_user_info,
    get_top_parrains, get_filleuls,
    get_palier_atteint, get_prochain_palier
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.ml_model import global_model_data
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from core.payments import ABONNEMENTS


# ⚠️ Remplace par le vrai nom de ton bot
BOT_USERNAME = "MonPronosticFootball_bot"


def enregistrer_user_handlers(bot):

    # =========================================================
    # /myid
    # =========================================================
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        bot.reply_to(message, f"ID : {message.from_user.id}")


    # =========================================================
    # /langue
    # =========================================================
    @bot.message_handler(commands=['langue', 'language'])
    def cmd_langue(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for code, nom in LANGUES_DISPONIBLES.items():
            markup.add(telebot.types.InlineKeyboardButton(
                nom,
                callback_data=f"lang|{code}"
            ))

        bot.reply_to(
            message,
            get_text("choix_langue", langue),
            reply_markup=markup
        )


    # =========================================================
    # CALLBACK LANGUE
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        from telegram_bot.menu_handlers import envoyer_menu_principal

        user_id = call.from_user.id
        langue = call.data.split("|")[1]

        if set_langue(user_id, langue):
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(
                call.message.chat.id,
                get_text("langue_changee", langue)
            )
            envoyer_menu_principal(call.message.chat.id, user_id, bot)
        else:
            bot.answer_callback_query(call.id, "Erreur")


    # =========================================================
    # /notif_on, /notif_off
    # =========================================================
    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if activer_notifications(user_id):
            bot.reply_to(message, get_text("notifs_activees", langue))


    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if desactiver_notifications(user_id):
            bot.reply_to(message, get_text("notifs_desactivees", langue))


    @bot.callback_query_handler(func=lambda call: call.data.startswith("notif|"))
    def traiter_notif_callback(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        action = call.data.split("|")[1]

        if action == "on":
            if activer_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_activees", langue))
        elif action == "off":
            if desactiver_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_desactivees", langue))


    # =========================================================
    # CALLBACK PARRAINAGE : Classement
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "parr|classement")
    def parrainage_classement(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)

        top = get_top_parrains(limite=10)

        if not top:
            bot.answer_callback_query(call.id, "Aucun parrain")
            bot.send_message(
                call.message.chat.id,
                "CLASSEMENT DES PARRAINS\n\nAucun parrain pour l'instant. Sois le premier !"
            )
            return

        bot.answer_callback_query(call.id, "OK")

        texte = "CLASSEMENT DES PARRAINS\n\n"
        for i, p in enumerate(top, 1):
            texte += f"{i}. {p['first_name'] or 'Anonyme'} - {p['nb_filleuls']} filleul(s)\n"

        bot.send_message(call.message.chat.id, texte)


    # =========================================================
    # CALLBACK PARRAINAGE : Mes filleuls
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "parr|filleuls")
    def parrainage_mes_filleuls(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)

        filleuls = get_filleuls(user_id, limite=20)

        if not filleuls:
            bot.answer_callback_query(call.id, "Aucun filleul")
            bot.send_message(
                call.message.chat.id,
                "MES FILLEULS\n\nTu n'as pas encore de filleul."
            )
            return

        bot.answer_callback_query(call.id, "OK")

        texte = f"MES FILLEULS ({len(filleuls)})\n\n"
        for i, f in enumerate(filleuls, 1):
            date = f['date_inscription'].strftime('%d/%m/%Y') if f['date_inscription'] else '?'
            texte += f"{i}. {f['first_name'] or 'Anonyme'} - {date}\n"

        bot.send_message(call.message.chat.id, texte)


    # =========================================================
    # BOUTONS DU MENU (texte)
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Parrainage", "Referral", "Bosangisi",
        "Matchs du jour", "Today's matches", "Masano ya lelo",
        "Statistiques", "Statistics", "Mituya",
        "Historique", "History", "Lisolo",
        "Notifications", "Nsango",
        "Langue", "Language", "Monoko",
        "Passer Premium", "Go Premium", "Kende Premium",
        "Faire un Pronostic", "Make a Prediction", "Sala Bokano",
    ])
    def handle_menu_buttons(message):
        text = message.text
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        # --- Parrainage ---
        if text == get_text("btn_parrainage", langue):
            code = f"REF{user_id}"
            lien = f"https://t.me/{BOT_USERNAME}?start={code}"
            nb_filleuls = compter_filleuls(user_id)

            texte = get_text(
                "parrainage_titre", langue,
                lien=lien,
                code=code,
                nb_filleuls=nb_filleuls
            )

            palier = get_palier_atteint(nb_filleuls)
            if palier:
                texte += f"\n\n🏆 {get_text('parrainage_palier_actuel', langue, nom=palier['nom'], bonus=palier['bonus'])}"

            prochain = get_prochain_palier(nb_filleuls)
            if prochain:
                texte += f"\n🎯 {get_text('parrainage_prochain_palier', langue, nom=prochain['nom'], restant=prochain['restant'], bonus=prochain['bonus'])}"

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "🏆 Classement",
                    callback_data="parr|classement"
                ),
                telebot.types.InlineKeyboardButton(
                    "👥 Mes filleuls",
                    callback_data="parr|filleuls"
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "📤 Partager",
                    url=f"https://t.me/share/url?url={lien}&text=Rejoins ce bot de pronostics !"
                )
            )

            bot.reply_to(message, texte, reply_markup=markup)

        # --- Matchs du jour ---
        elif text == get_text("btn_matchs_jour", langue):
            bot.reply_to(message, "Recherche des matchs du jour...")

            try:
                from telegram_bot.menu_handlers import _charger_modele_si_necessaire
                if not _charger_modele_si_necessaire(message, bot):
                    return

                matchs = get_matchs_du_jour()
                is_prem = est_premium(user_id)
                
                # Free : 15 matchs max SANS reco / Premium : tous les matchs avec recos
                nb_max = None if is_prem else 15

                texte = formater_matchs_du_jour(
                    matchs, 
                    langue,
                    est_premium=is_prem,
                    nb_max=nb_max
                )
                bot.send_message(message.chat.id, texte)
            except Exception as e:
                import traceback
                print(f"ERREUR MATCHS DU JOUR :\n{traceback.format_exc()}")
                bot.send_message(message.chat.id, f"Erreur : {str(e)[:200]}")

        # --- Statistiques ---
        elif text == get_text("btn_stats", langue):
            prec = global_model_data.get('precision', 0.5)
            length = len(global_model_data.get('df', []))
            bot.reply_to(
                message,
                get_text("stats_ia", langue, nb_matchs=length, precision=round(prec * 100, 2))
            )

        # --- Historique ---
        elif text == get_text("btn_historique", langue):
            try:
                hist = pd.read_csv(FICHIER_HISTORIQUE)
                last_5 = hist.tail(5)
                texte = get_text("historique_titre", langue)
                for i, (_, row) in enumerate(last_5.iterrows(), 1):
                    texte += (
                        f"{i}. {row['Match']}\n"
                        f"   {row['Date_Consultation']}\n"
                        f"   {row['Pronostic_1N2']}\n"
                        f"   Score : {row['Score_Exact']}\n\n"
                    )
                bot.reply_to(message, texte)
            except FileNotFoundError:
                bot.reply_to(message, get_text("historique_vide", langue))

        # --- Notifications ---
        elif text == get_text("btn_notifs", langue):
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    get_text("bouton_activer", langue),
                    callback_data="notif|on"
                ),
                telebot.types.InlineKeyboardButton(
                    get_text("bouton_desactiver", langue),
                    callback_data="notif|off"
                ),
            )
            bot.reply_to(
                message,
                get_text("notifs_titre", langue),
                reply_markup=markup
            )

        # --- Langue ---
        elif text == get_text("btn_langue", langue):
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for code, nom in LANGUES_DISPONIBLES.items():
                markup.add(telebot.types.InlineKeyboardButton(
                    nom,
                    callback_data=f"lang|{code}"
                ))
            bot.reply_to(
                message,
                get_text("choix_langue", langue),
                reply_markup=markup
            )

        # --- Premium (3 choix) ---
        elif text == get_text("btn_premium", langue):
            if est_premium(user_id):
                bot.reply_to(message, get_text("premium_actif", langue))
                return

            # 3 choix de paiement
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    get_text("btn_pay_stars", langue),
                    callback_data="pay|stars"
                ),
                telebot.types.InlineKeyboardButton(
                    get_text("btn_pay_mobile", langue),
                    callback_data="pay|mobile"
                ),
                telebot.types.InlineKeyboardButton(
                    get_text("btn_pay_code", langue),
                    callback_data="pay|code"
                ),
            )

            bot.reply_to(
                message,
                get_text("premium_choix_titre", langue),
                reply_markup=markup
            )

        # --- Faire un Pronostic ---
        elif text == get_text("btn_pronostic", langue):
            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
                )
                return

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Choisir avec des boutons",
                    callback_data="start_inline_prono"
                )
            )
            bot.reply_to(
                message,
                get_text("demande_affiche", langue),
                reply_markup=markup
            )
