# core/utils/error_handler.py
"""
Capture globale des erreurs non gérées :

- Thread principal (``sys.excepthook``)
- Threads secondaires (``threading.excepthook``)
- Envoi Telegram détaillé via ``core.utils.logs``
- Fallback ``print`` si ``logs.py`` plante

À appeler une seule fois au démarrage via :func:`activer_capture_globale`.
"""

from __future__ import annotations

import sys
import threading
import traceback
from typing import Optional

_ancien_excepthook: Optional[object] = sys.excepthook
_ancien_threading_excepthook: Optional[object] = getattr(threading, "excepthook", None)


def _extraire_info_thread(thread: threading.Thread | None = None) -> dict[str, str | int]:
    """Extrait des informations du thread pour le contexte d'erreur.

    Args:
        thread: Thread à inspecter. Si None, utilise le thread courant.

    Returns:
        Dictionnaire avec ``thread_name`` et ``thread_ident``.
    """
    if thread is not None:
        return {"thread_name": thread.name, "thread_ident": thread.ident}
    current = threading.current_thread()
    return {"thread_name": current.name, "thread_ident": current.ident}


def _gerer_exception_non_geree(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[traceback.TracebackException],
) -> None:
    """Capture toutes les erreurs non gérées du thread principal.

    Laisse passer KeyboardInterrupt (Ctrl+C) pour ne pas bloquer l'arrêt.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        if _ancien_excepthook is not None:
            _ancien_excepthook(exc_type, exc_value, exc_traceback)
        return

    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"🔥 ERREUR GLOBALE NON GÉRÉE :\n{tb}", file=sys.stderr)

    try:
        from core.utils.logs import log_error
        log_error(
            message=f"Erreur non gérée : {exc_type.__name__} - {exc_value}",
            module="GLOBAL",
            exception=exc_value,
            extra=_extraire_info_thread(),
        )
    except Exception as e:
        print(f"⚠️ Impossible d'envoyer l'erreur à l'admin : {e}", file=sys.stderr)
        print(tb, file=sys.stderr)


def _gerer_exception_thread(args: tuple) -> None:
    """Capture les erreurs dans les threads secondaires.

    Args:
        args: Tuple (exc_type, exc_value, exc_traceback, thread) fourni par
              threading.excepthook.
    """
    if not args or len(args) < 3:
        return
    exc_type, exc_value, exc_traceback = args[0], args[1], args[2]
    thread = getattr(args, "thread", None) if hasattr(args, "thread") else None
    _gerer_exception_non_geree(exc_type, exc_value, exc_traceback)


def activer_capture_globale() -> None:
    """Active le filet de sécurité global.

    À appeler UNE SEULE FOIS au démarrage de l'application.
    """
    sys.excepthook = _gerer_exception_non_geree
    threading.excepthook = _gerer_exception_thread  # type: ignore[assignment]
    print("✅ Système de capture globale des erreurs activé.")
