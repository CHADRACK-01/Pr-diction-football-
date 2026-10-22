import traceback
from core.utils.error_handler import envoyer_erreur_admin


def log_info(message, module="BOT"):
    """Log une information normale."""
    print(f"[{module}] ℹ️ {message}")


def log_warning(message, module="BOT"):
    """Log un avertissement."""
    print(f"[{module}] ⚠️ {message}")


def log_error(message, module="BOT", exception=None):
    """
    Log une erreur avec la trace complète.
    Envoie TOUJOURS l'erreur sur Telegram via le gestionnaire global.
    """
    print(f"[{module}] ❌ {message}")
    
    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"[{module}] 🔥 TRACEBACK:\n{trace}")
        
    # On prépare le texte pour l'admin (on évite de dépasser la limite Telegram)
    texte_alerte = f"{message}\n\n{trace}" if trace else message
    
    # On envoie l'alerte via le gestionnaire d'erreurs global
    envoyer_erreur_admin(texte_alerte, context=module)


def log_canal_action(action, succes, details=""):
    """Log spécifique pour les actions sur le canal."""
    statut = "✅" if succes else "❌"
    print(f"[CANAL] {statut} {action} - {details}")
