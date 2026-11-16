# telegram_bot/cashout_handlers.py
"""
Handler pour la commande /cashout.
Simule le cash-out d'un pari.
"""

import telebot
from core.cashout import get_cote_actuelle, simuler_cashout, formater_cashout
from core.utils.logs import log_info, log_error


def enregistrer_cashout_handlers(bot):

    @bot.message_handler(commands=['cashout'])
    def cmd_cashout(message):
        args = message.text.split()
        
        if len(args) < 5:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/cashout EQUIPE1 vs EQUIPE2 MISE COTE_INITIALE</code>\n"
                "Exemple : <code>/cashout Chelsea vs Arsenal 10000 2.50</code>",
                parse_mode="HTML"
            )
            return

        try:
            # Récupérer les équipes (les 3 premiers mots après la commande)
            match_str = " ".join(args[1:4])  # Chelsea vs Arsenal
            if " vs " not in match_str.lower():
                bot.reply_to(message, "❌ Format : <code>/cashout Equipe1 vs Equipe2 MISE COTE</code>", parse_mode="HTML")
                return

            equipes = match_str.split(" vs ")
            home_team = equipes[0].strip()
            away_team = equipes[1].strip()

            mise = float(args[4])
            cote_initiale = float(args[5]) if len(args) > 5 else 2.00

            bot.reply_to(message, f"⏳ Calcul du cash-out pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            # Récupérer la cote actuelle
            cote_actuelle = get_cote_actuelle(home_team, away_team)
            
            if cote_actuelle is None:
                bot.reply_to(message, "❌ Impossible de récupérer la cote actuelle. Vérifie le nom des équipes ou le sport.")
                return

            # Calculer le cash-out
            cashout = simuler_cashout(mise, cote_initiale, cote_actuelle)

            texte = formater_cashout(home_team, away_team, mise, cote_initiale, cote_actuelle, cashout)
            bot.reply_to(message, texte, parse_mode="HTML")

        except ValueError:
            bot.reply_to(message, "❌ La mise et la cote doivent être des nombres.")
        except Exception as e:
            log_error("Erreur commande /cashout", "CASHOUT", exception=e)
            bot.reply_to(message, "❌ Erreur lors du calcul.")
