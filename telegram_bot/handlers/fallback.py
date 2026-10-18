import telebot
from users import get_langue, est_banni
from core.translations import get_text
from telegram_bot.handlers.start import envoyer_menu_principal

def enregistrer_fallback_handlers(bot):
    # Le fallback est désactivé pour éviter les conflits avec les autres handlers.
    # On le réactivera quand tous les boutons seront stables.
    pass
