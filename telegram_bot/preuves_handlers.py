"""
Handlers de la commande /preuves.

Affiche un historique vérifiable des derniers résultats de pronostics
(gagnés, perdus, taux de réussite) sous forme de message HTML.
Commande réservée aux administrateurs pour l'instant.
"""
import telebot
from users.admin import est_administrateur
from users.db import db_fetchall
from core.utils.logs import log_info, log_warning


def enregistrer_preuves_handlers(bot):

    @bot.message_handler(commands=['preuves'])
    def cmd_preuves(message):
        user_id = message.from_user.id
        try:
            if not est_administrateur(user_id):
                log_warning(message="Tentative d'accès à /preuves refusée", module="PREUVES", user_context={"user_id": user_id})
                bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
                return

            resultats = db_fetchall(
                "SELECT est_gagnant FROM resultats_pronostics ORDER BY id DESC LIMIT 30",
                db_context={'table': 'resultats_pronostics', 'operation': 'preuves'},
            )

            if not resultats:
                bot.reply_to(message, "📊 HISTORIQUE VÉRIFIABLE\n\nAucun résultat enregistré pour le moment.", parse_mode='HTML')
                log_info("Commande /preuves : aucun résultat", "PREUVES", user_context={"user_id": user_id})
                return

            # row[0] fonctionne pour un tuple comme pour un sqlite3.Row ;
            # les valeurs NULL ne valent ni 1 ni 0 et sont donc ignorées.
            gagnes = sum(1 for row in resultats if row[0] == 1)
            perdus = sum(1 for row in resultats if row[0] == 0)
            total = gagnes + perdus
            taux = round((gagnes / total) * 100) if total > 0 else 0

            texte = (
                "📊 HISTORIQUE VÉRIFIABLE\n\n"
                "30 derniers jours :\n"
                f"✅ Gagnés : {gagnes}\n"
                f"❌ Perdus : {perdus}\n"
                f"🎯 Taux de réussite : {taux}%\n\n"
                "Ces résultats sont issus de la base de données et ne peuvent pas être modifiés."
            )

            try:
                bot.reply_to(message, texte, parse_mode='HTML')
                log_info("Commande /preuves envoyée", "PREUVES", user_context={"user_id": user_id})
            except Exception as e:
                log_warning(message=f"Erreur d'envoi du message /preuves pour {user_id}", module="PREUVES", user_context={"user_id": user_id}, exception=e)
        except Exception as e:
            log_warning(message=f"Erreur commande /preuves pour {user_id}", module="PREUVES", user_context={"user_id": user_id}, exception=e)
