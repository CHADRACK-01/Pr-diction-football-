import telebot

from users import get_langue, peut_faire_pronostic, get_limite_jour, est_banni
from core.translations import get_text


def enregistrer_inline_handlers(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "start_inline_prono")
    def start_inline_prono(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.answer_callback_query(call.id, "Tu es banni.")
            return

        if not peut_faire_pronostic(user_id):
            bot.answer_callback_query(call.id, "Limite atteinte")
            bot.send_message(
                call.message.chat.id,
                get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
            )
            return

        bot.answer_callback_query(call.id, "OK")

        # On supprime la recherche par lettres A-Z, on demande directement la saisie
        bot.send_message(
            call.message.chat.id,
            "⚽ **Tape ton pronostic** :\n\n"
            "Format : `Équipe A vs Équipe B`\n\n"
            "Exemples :\n"
            "• `PSG vs Marseille`\n"
            "• `Real Madrid vs Barcelona`\n"
            "• `Man City vs Arsenal`",
            parse_mode="Markdown"
        )
