# core/utils/error_handler.py
"""
Capture globale des erreurs non gérées :
- Thread principal (sys.excepthook)
- Threads secondaires (threading.excepthook)
- Envoi Telegram détaillé via logs.py
- Fallback print si logs.py plante
"""

import sys
import threading
import traceback

_ancien_excepthook = sys.excepthook
_ancien_threading_excepthook = getattr(threading, "excepthook", None)


def _extraire_info_thread(thread=None):
    """Extrait des informations du thread pour le contexte."""
    info = {}
    if thread:
        info["thread_name"] = thread.name
        info["thread_ident"] = thread.ident
    else:
        current = threading.current_thread()
        info["thread_name"] = current.name
        info["thread_ident"] = current.ident
    return info


def _gerer_exception_non_geree(exc_type, exc_value, exc_traceback):
    """Capture TOUTES les erreurs non gérées."""
    # Ctrl+C : laisser passer
    if issubclass(exc_type, KeyboardInterrupt):
        _ancien_excepthook(exc_type, exc_value, exc_traceback)
        return

    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"🔥 ERREUR GLOBALE NON GÉRÉE :\n{tb}", file=sys.stderr)

    # On essaie d'envoyer via logs.py
    try:
        from core.utils.logs import log_error
        log_error(
            message=f"Erreur non gérée : {exc_type.__name__} - {exc_value}",
            module="GLOBAL",
            exception=exc_value,
            extra=_extraire_info_thread(),
        )
    except Exception as e:
        # Fallback : si logs.py lui-même plante, on imprime au moins
        print(f"⚠️ Impossible d'envoyer l'erreur à l'admin : {e}", file=sys.stderr)
        print(tb, file=sys.stderr)


def _gerer_exception_thread(args):
    """Capture les erreurs dans les threads secondaires."""
    if not args or len(args) < 3:
        return
    exc_type, exc_value, exc_traceback = args[0], args[1], args[2]
    thread = getattr(args, "thread", None) if hasattr(args, "thread") else None
    _gerer_exception_non_geree(exc_type, exc_value, exc_traceback)


def activer_capture_globale():
    """Active le filet de sécurité global. À appeler UNE SEULE FOIS au démarrage."""
    sys.excepthook = _gerer_exception_non_geree
    threading.excepthook = _gerer_exception_thread
    print("✅ Système de capture globale des erreurs activé.")
