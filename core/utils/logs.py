import traceback
from core.utils.error_handler import envoyer_erreur_admin

def log_info(message, module="BOT"):
    """Log une information normale."""
    print(f"[{module}] ℹ️ {message}")

def log_warning(message, module="BOT"):
    """Log un avertissement."""
    print(f"[{module}] ⚠️ {message}")

def log_error(message, module="BOT", exception=None, notifier_telegram=False):
    """
    Log une erreur avec la trace complète.
    Si notifier_telegram=True, envoie aussi l'erreur sur ton Telegram.
    """
    print(f"[{module}] ❌ {message}")
    
    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"[{module}] 🔥 TRACEBACK:\n{trace}")
        
    if notifier_telegram:
        texte = f"{message}\n\n{trace}"
        envoyer_erreur_admin(texte, context=module)

def log_canal_action(action, succes, details=""):
    """Log spécifique pour les actions sur le canal."""
    statut = "✅" if succes else "❌"
    print(f"[CANAL] {statut} {action} - {details}")
