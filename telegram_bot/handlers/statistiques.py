import telebot
from users import get_langue
from core.translations import get_text
from core.ml_model import global_model_data

def enregistrer_statistiques_handlers(bot):
    @bot.message_handler(func=lambda m: m.from_user and m.text in [
        "Statistiques", "Statistics", "Mituya"
    ])
    def handle_statistiques(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        prec = global_model_data.get('precision', 0.5)
        length = len(global_model_data.get('df', []))
        bot.reply_to(
            message,
            get_text("stats_ia", langue, nb_matchs=length, precision=round(prec * 100, 2))
        )
