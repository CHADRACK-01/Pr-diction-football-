# Package telegram_bot - Handlers et interface Telegram
from telegram_bot.codes_promo_handlers import enregistrer_codes_promo_handlers
from telegram_bot.utilisation_code_handlers import enregistrer_utilisation_code_handlers

# Dans handlers_modules :
("CodesPromo", enregistrer_codes_promo_handlers),
("UtilisationCode", enregistrer_utilisation_code_handlers),
