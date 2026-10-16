import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import telebot
from flask import Flask, request

from config import TOKEN
from users import initialiser_tables
from telegram_bot.handlers import enregistrer_handlers


bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Enregistrer les handlers Telegram
enregistrer_handlers(bot)


# =========================================================
# WEBHOOK TELEGRAM
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# =========================================================
# ROUTE DE BASE
# =========================================================
@app.route('/')
def index():
    return "Bot opérationnel !", 200


# =========================================================
# INITIALISATION AU BOOT
# =========================================================
initialiser_tables()
print("✅ Bot prêt. Le modèle se chargera à la première demande.")
