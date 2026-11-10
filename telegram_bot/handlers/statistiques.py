import telebot
from users import get_langue
from core.ml_model import global_model_data
from core.utils.logs import log_warning


def enregistrer_statistiques_handlers(bot):
    
    @bot.message_handler(func=lambda m: m.text == "📊 Statistiques")
    def handle_statistiques(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        # Vérifier que les modèles sont chargés
        modeles = global_model_data.get('modeles_par_competition')
        if not modeles:
            log_warning(f"Statistiques demandées par {user_id} mais modèle non chargé", "STATS")
            bot.reply_to(
                message,
                "📊 **Statistiques indisponibles**\n\n"
                "Le modèle est en cours de chargement. Réessaie dans quelques instants.\n"
                "Si le problème persiste, l'administrateur est prévenu automatiquement."
            )
            return
        
        # Récupération des vraies clés
        prec = global_model_data.get('precision_moyenne', 0.58)
        total_matchs = global_model_data.get('total_matchs', 0)
        nb_competitions = len(modeles)
        
        # Calcul du nombre total de marchés (5 par compétition normalement)
        nb_marches = sum(len(m) for m in modeles.values())
        
        texte = (
            f"📊 **STATISTIQUES DU MODÈLE IA**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🧠 **Modèle** : LightGBM + Calibration Isotonic\n"
            f"📚 **Compétitions supportées** : {nb_competitions}\n"
            f"🎯 **Marchés prédits** : {nb_marches}\n"
            f"📈 **Matchs d'entraînement** : {total_matchs:,}\n"
            f"🎯 **Précision moyenne** : {round(prec*100, 2)}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **Marchés disponibles** :\n"
            f"• 🛡️ Double Chance (1X, X2, 12)\n"
            f"• 🎯 BTTS (Les 2 marquent)\n"
            f"• 🥅 Over/Under 2.5 buts\n"
            f"• ⏱️ Mi-temps la plus prolifique\n"
            f"• 🏁 1N2 à la mi-temps\n\n"
            f"💡 _Les marchés Mi-temps sont indicatifs._"
        )
        
        try:
            bot.reply_to(message, texte, parse_mode="Markdown")
        except Exception as e:
            log_warning(f"Impossible d'afficher les stats en Markdown pour {user_id} : {e}", "STATS")
            # Fallback sans Markdown
            try:
                bot.reply_to(message, texte.replace("**", "").replace("_", ""))
            except Exception as e2:
                log_warning(f"Impossible d'afficher les stats (fallback) pour {user_id} : {e2}", "STATS")
