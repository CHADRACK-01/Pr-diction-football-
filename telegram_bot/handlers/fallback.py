import telebot
from users import get_langue, est_banni
from core.translations import get_text
from telegram_bot.handlers.start import envoyer_menu_principal

def enregistrer_fallback_handlers(bot):
    @bot.message_handler(func=lambda message: not message.text.startswith('/'))
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        # ⚠️ On ignore les boutons qui ont leur propre handler
        textes_ignores = [
            "Faire un Pronostic", "Make a Prediction", "Sala Bokano",
            "Matchs du jour", "Today's matches", "Masano ya lelo",
            "Coupons", "Coupons du jour", "Coupons ya lelo",
            "Top affiches", "Affiches du jour", "Affiches ya lelo",
            "Historique", "History", "Lisolo",
            "Statistiques", "Statistics", "Mituya",
            "Notifications", "Nsango",
            "Passer Premium", "Go Premium", "Kende Premium",
            "Parrainage", "Referral", "Bosangisi",
            "Langue", "Language", "Monoko",
            "Panneau Admin"
        ]
        
        if message.text in textes_ignores:
            return  # On laisse les autres handlers faire le travail

        # On ignore si l'utilisateur est en session admin
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        if user_id in ADMIN_SESSIONS:
            return

        # Si c'est un vrai message inconnu, on affiche le fallback
        bot.reply_to(message, get_text("fallback", langue))
        envoyer_menu_principal(message.chat.id, user_id, bot)
