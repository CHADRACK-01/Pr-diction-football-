import sys
import traceback
import telebot
from datetime import datetime

# ⚠️ Identifiants pour les alertes
ADMIN_ID = 8653408729 
BOT_TOKEN = "8443191637:AAGcCknBZDg1o0NBeL8czLt0SsQ4c2LEMvY"

def envoyer_erreur_admin(message_erreur, context="Global"):
    """Envoie une alerte d'erreur directement sur le Telegram de l'admin."""
    try:
        bot_alerte = telebot.TeleBot(BOT_TOKEN, threaded=False)
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        
        # On tronque pour ne pas dépasser la limite de Telegram (4096 caractères)
        erreur_courte = message_erreur[:3500]
        
        texte = (
            f"🚨 **ALERTE ERREUR** 🚨\n\n"
            f"📅 Date : {date_str}\n"
            f"📌 Contexte : {context}\n\n"
            f"```python\n{erreur_courte}\n```"
        )
        bot_alerte.send_message(ADMIN_ID, texte, parse_mode="Markdown")
    except Exception as e:
        # Si même l'alerte plante, on l'écrit dans les logs Render
        print(f"⚠️ Impossible d'envoyer l'alerte Telegram : {e}")

def gerer_exception_non_geree(exc_type, exc_value, exc_traceback):
    """
    Capture TOUTES les erreurs non gérées par le bot.
    Empêche le bot de crasher et envoie l'erreur sur Telegram.
    """
    # Si c'est une interruption clavier (Ctrl+C), on laisse faire
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # On formate la trace de l'erreur
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # On l'affiche dans les logs Render
    print(f"🔥 ERREUR GLOBALE NON GÉRÉE :\n{tb}")
    
    # On envoie sur Telegram
    envoyer_erreur_admin(tb, context="Erreur Globale (Non gérée)")

def activer_capture_globale():
    """À appeler UNE SEULE FOIS au démarrage du bot pour activer le filet de sécurité."""
    sys.excepthook = gerer_exception_non_geree
    print("✅ Système de capture globale des erreurs activé.")
