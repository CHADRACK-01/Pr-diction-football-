import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

import telebot
from flask import Flask, request

from config import TOKEN
from telegram_bot.handlers import enregistrer_handlers


bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Enregistrer les handlers Telegram
enregistrer_handlers(bot)


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route('/')
def index():
    return "Bot opérationnel !", 200


# =========================================================
# INITIALISATION AU BOOT
# =========================================================
print("🚀 Bot prêt (init différée).")
# NE PAS appeler initialiser_tables() ici : ça bloque le démarrage de gunicorn
