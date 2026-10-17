import traceback

def log_info(message, module="BOT"):
    """Log une information normale."""
    print(f"[{module}] ℹ️ {message}")

def log_warning(message, module="BOT"):
    """Log un avertissement."""
    print(f"[{module}] ⚠️ {message}")

def log_error(message, module="BOT", exception=None):
    """Log une erreur avec la trace complète si fournie."""
    print(f"[{module}] ❌ {message}")
    if exception:
        trace = traceback.format_exc()
        print(f"[{module}] 🔥 TRACEBACK:\n{trace}")

def log_canal_action(action, succes, details=""):
    """Log spécifique pour les actions sur le canal."""
    statut = "✅" if succes else "❌"
    print(f"[CANAL] {statut} {action} - {details}")
