import telebot
from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour
from core.translations import get_text
from core.utils.logs import log_error


def enregistrer_pronostic_handlers(bot):

    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Faire un Pronostic", "Make a Prediction", "Sala Bokano"
    ])
    def handle_pronostic(message):
        print(f"[PRONOSTIC] Bouton cliqué par {message.from_user.id}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        if not peut_faire_pronostic(user_id):
            bot.reply_to(
                message,
                get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
            )
            return

        bot.reply_to(
            message,
            "⚽ Tape ton pronostic :\n\n"
            "Format : Equipe A vs Equipe B\n\n"
            "Exemples :\n"
            "• PSG vs Marseille\n"
            "• Real Madrid vs Barcelona\n"
            "• Man City vs Arsenal"
        )
