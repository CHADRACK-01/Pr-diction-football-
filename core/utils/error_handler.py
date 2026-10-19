import traceback
import functools
from datetime import datetime
import telebot

# On met le Token et l'ID Admin ici pour éviter les imports circulaires
# ⚠️ REMPLACE PAR TES VRAIES VALEURS
ADMIN_ID = 8653408729 
BOT_TOKEN = "8443191637:AAGcCknBZDg1o0NBeL8czLt0SsQ4c2LEMvY"

def envoyer_erreur_admin(message_erreur, context=""):
    """Envoie une alerte d'erreur directement sur le Telegram de l'admin."""
    try:
        bot_alerte = telebot.TeleBot(BOT_TOKEN, threaded=False)
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        
        texte = (
            f"🚨 **ALERTE ERREUR** 🚨\n\n"
            f"📅 Date : {date_str}\n"
            f"📌 Contexte : {context}\n\n"
            f"```python\n{message_erreur[:3500]}\n```"
        )
        bot_alerte.send_message(ADMIN_ID, texte, parse_mode="Markdown")
    except Exception as e:
        # Si même l'alerte plante, on l'écrit dans les logs Render
        print(f"⚠️ Impossible d'envoyer l'alerte Telegram : {e}")

def capturer_erreurs(context="Général"):
    """
    Décorateur à mettre au-dessus de n'importe quelle fonction.
    Si la fonction plante, l'erreur est capturée, envoyée sur Telegram,
    et le bot continue de fonctionner.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 1. On récupère la trace complète de l'erreur
                tb = traceback.format_exc()
                
                # 2. On l'affiche dans les logs Render (pour l'historique)
                print(f"❌ ERREUR CAPTURÉE dans [{context}] -> {func.__name__} : {e}")
                print(f"🔥 TRACEBACK:\n{tb}")
                
                # 3. On envoie l'alerte sur Telegram
                envoyer_erreur_admin(tb, context=f"{context} -> {func.__name__}")
                
                # 4. On ne relance pas l'erreur (le bot continue)
                return None
        return wrapper
    return decorator
