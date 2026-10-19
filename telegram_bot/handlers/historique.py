import telebot
import pandas as pd
from config import FICHIER_HISTORIQUE
from users import get_langue
from core.translations import get_text
from core.utils.logs import log_error

def enregistrer_historique_handlers(bot):
    
    @bot.message_handler(func=lambda m: m.text == "#HISTO")
    def handle_historique(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        try:
            hist = pd.read_csv(FICHIER_HISTORIQUE)
            last_5 = hist.tail(5)
            texte = get_text("historique_titre", langue)
            
            for i, (_, row) in enumerate(last_5.iterrows(), 1):
                texte += (
                    f"{i}. {row['Match']}\n"
                    f"   {row['Date_Consultation']}\n"
                    f"   {row['Pronostic_1N2']}\n"
                    f"   Score : {row['Score_Exact']}\n\n"
                )
                
            bot.reply_to(message, texte)
            
        except FileNotFoundError:
            bot.reply_to(message, get_text("historique_vide", langue))
        except Exception as e:
            log_error(f"Erreur historique : {e}", "HISTORIQUE", e)
            bot.reply_to(message, "Erreur lors de la récupération de l'historique.")
