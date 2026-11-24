"""Routes Flask publiques et webhook Telegram."""

import hmac
import os
import threading

import telebot
from flask import request

from core.utils.logs import log_error, log_warning


def register_public_routes(app, *, bot, initialiser_bdd_si_necessaire):
    @app.route("/webhook", methods=["POST"])
    def webhook():
        secret_attendu = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
        secret_recu = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret_attendu or not hmac.compare_digest(secret_attendu, secret_recu):
            log_warning(
                message="Webhook refusé : secret invalide ou absent",
                module="FLASK",
                extra={"ip": request.remote_addr},
            )
            return "Forbidden", 403

        try:
            initialiser_bdd_si_necessaire()
        except Exception as exc:
            log_error("Initialisation DB impossible depuis le webhook", "FLASK", exception=exc)
            return "Service unavailable", 503

        try:
            update = telebot.types.Update.de_json(request.get_data().decode("UTF-8"))
            if not update:
                return "OK", 200

            def traiter_update():
                try:
                    bot.process_new_updates([update])
                except Exception as exc:
                    log_error(
                        message="Erreur update Telegram",
                        module="FLASK",
                        exception=exc,
                    )

            threading.Thread(target=traiter_update, daemon=True).start()
        except Exception as exc:
            log_error("Erreur de parsing du webhook Telegram", "FLASK", exception=exc)
        return "OK", 200

    @app.route("/")
    def index():
        return "Bot operationnel !", 200

    @app.route("/health")
    def health():
        try:
            from users.database import db_fetchone

            if db_fetchone("SELECT 1"):
                return "✅ OK", 200
            return "❌ DB muette", 503
        except Exception as exc:
            log_error("Santé DB inaccessible", "FLASK", exception=exc)
            return "❌ DB inaccessible", 503
