import sys
import traceback
import threading
from core.utils.logs import log_error

# On garde une référence à l'ancien excepthook pour ne pas le casser
_ancien_excepthook = sys.excepthook


def _gerer_exception_non_geree(exc_type, exc_value, exc_traceback):
    """
    Capture TOUTES les erreurs non gérées par le bot.
    Envoie l'erreur à l'admin via Telegram.
    """
    # Si c'est une interruption clavier (Ctrl+C), on laisse faire
    if issubclass(exc_type, KeyboardInterrupt):
        _ancien_excepthook(exc_type, exc_value, exc_traceback)
        return

    # On formate la trace complète
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # On affiche dans les logs Render (pour le débogage local)
    print(f"🔥 ERREUR GLOBALE NON GÉRÉE :\n{tb}")
    
    # On envoie à l'admin via notre fonction centralisée de logs.py
    log_error(
        message=f"Erreur non gérée : {exc_type.__name__} - {exc_value}",
        module="GLOBAL",
        exception=exc_value
    )


def _gerer_exception_thread(args):
    """Capture les erreurs dans les threads séparés."""
    exc_type, exc_value, exc_traceback = args
    _gerer_exception_non_geree(exc_type, exc_value, exc_traceback)


def activer_capture_globale():
    """
    Active le filet de sécurité global.
    À appeler UNE SEULE FOIS au démarrage du bot (dans app.py).
    """
    # 1. Capture les erreurs du thread principal
    sys.excepthook = _gerer_exception_non_geree
    
    # 2. Capture les erreurs des threads (scheduler, etc.)
    threading.excepthook = _gerer_exception_thread
    
    print("✅ Système de capture globale des erreurs activé.")
