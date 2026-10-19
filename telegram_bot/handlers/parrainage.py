import telebot
from users import (
    get_langue, get_user_info, compter_filleuls,
    get_top_parrains, get_filleuls, get_palier_atteint, get_prochain_palier
)
from core.translations import get_text

BOT_USERNAME = "MonPronosticFootball_bot"

def enregistrer_parrainage_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "#PARRAINAGE")
    def handle_parrainage(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        code = f"REF{user_id}"
        lien = f"https://t.me/{BOT_USERNAME}?start={code}"
        nb_filleuls = compter_filleuls(user_id)

        texte = get_text(
            "parrainage_titre", langue,
            lien=lien, code=code, nb_filleuls=nb_filleuls
        )

        palier = get_palier_atteint(nb_filleuls)
        if palier:
            texte += f"\n\n🏆 {get_text('parrainage_palier_actuel', langue, nom=palier['nom'], bonus=palier['bonus'])}"

        prochain = get_prochain_palier(nb_filleuls)
        if prochain:
            texte += f"\n🎯 {get_text('parrainage_prochain_palier', langue, nom=prochain['nom'], restant=prochain['restant'], bonus=prochain['bonus'])}"

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
        bot.reply_to(message, texte, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "parr|classement")
    def parrainage_classement(call):
        user_id = call.from_user.id
        top = get_top_parrains(limite=10)
        if not top:
            bot.answer_callback_query(call.id, "Aucun parrain")
            bot.send_message(call.message.chat.id, "CLASSEMENT DES PARRAINS\n\nAucun parrain pour l'instant. Sois le premier !")
            return
        bot.answer_callback_query(call.id, "OK")
        texte = "CLASSEMENT DES PARRAINS\n\n"
        for i, p in enumerate(top, 1):
            texte += f"{i}. {p['first_name'] or 'Anonyme'} - {p['nb_filleuls']} filleul(s)\n"
        bot.send_message(call.message.chat.id, texte)

    @bot.callback_query_handler(func=lambda call: call.data == "parr|filleuls")
    def parrainage_mes_filleuls(call):
        user_id = call.from_user.id
        filleuls = get_filleuls(user_id, limite=20)
        if not filleuls:
            bot.answer_callback_query(call.id, "Aucun filleul")
            bot.send_message(call.message.chat.id, "MES FILLEULS\n\nTu n'as pas encore de filleul.")
            return
        bot.answer_callback_query(call.id, "OK")
        texte = f"MES FILLEULS ({len(filleuls)})\n\n"
        for i, f in enumerate(filleuls, 1):
            date = f['date_inscription'].strftime('%d/%m/%Y') if f['date_inscription'] else '?'
            texte += f"{i}. {f['first_name'] or 'Anonyme'} - {date}\n"
        bot.send_message(call.message.chat.id, texte)
