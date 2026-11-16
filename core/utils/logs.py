# core/utils/logs.py
"""
Système de logs centralisé avec :
- Contexte utilisateur / API / DB enrichi
- Anti-flood par hash (déduplication 60s par défaut)
- Récap horaire des erreurs supprimées
- Envoi Telegram HTML échappé
- Fallback print si Telegram est down
- Détection automatique des handlers depuis la stack
- Métriques d'environnement (uptime, mémoire)
"""

import os
import sys
import time
import hashlib
import threading
import traceback
import requests
from datetime import datetime, timezone, timedelta
from collections import deque
from typing import Optional, Dict, Any

# =========================================================
# IMPORTS CONFIG (tolérants pour éviter les imports circulaires)
# =========================================================
try:
    from config import TOKEN, ADMIN_ID, LOG_DEDUP_WINDOW_SEC, LOG_RECAP_INTERVAL_SEC
except ImportError:
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
    try:
        ADMIN_ID = int(os.environ.get("ADMIN_ID", "8653408729"))
    except (ValueError, TypeError):
        ADMIN_ID = 8653408729
    LOG_DEDUP_WINDOW_SEC = 60
    LOG_RECAP_INTERVAL_SEC = 3600

TZ_KINSHASA = timezone(timedelta(hours=1))

# =========================================================
# ÉTAT GLOBAL (anti-flood, métriques, uptime)
# =========================================================
_START_TIME = time.time()
_LOCK = threading.Lock()

# Hash -> timestamp du dernier envoi
_DEDUP_CACHE: Dict[str, float] = {}
# Compteur des erreurs supprimées (module -> count)
_SUPPRIMEES: Dict[str, int] = {}
# Timestamp du dernier récap
_DERNIER_RECAP = time.time()

# File d'attente pour envois async (évite de bloquer)
_FILE_ENVOI: deque = deque(maxlen=500)


# =========================================================
# HELPERS INTERNES
# =========================================================
def _hash_erreur(module: str, message: str) -> str:
    """Hash court pour la déduplication."""
    cle = f"{module}|{message[:120]}"
    return hashlib.sha1(cle.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _doit_envoyer(hash_cle: str) -> bool:
    """
    Vérifie si on doit envoyer l'erreur (anti-flood).
    Retourne True si l'erreur n'a pas été envoyée récemment.
    """
    global _DERNIER_RECAP
    maintenant = time.time()
    with _LOCK:
        dernier = _DEDUP_CACHE.get(hash_cle, 0)
        if maintenant - dernier < LOG_DEDUP_WINDOW_SEC:
            # Flood : on incrémente le compteur de supprimées
            _SUPPRIMEES[hash_cle] = _SUPPRIMEES.get(hash_cle, 0) + 1
            return False
        _DEDUP_CACHE[hash_cle] = maintenant

        # Nettoyage du cache si trop gros
        if len(_DEDUP_CACHE) > 1000:
            seuil = maintenant - LOG_DEDUP_WINDOW_SEC * 10
            a_supprimer = [k for k, v in _DEDUP_CACHE.items() if v < seuil]
            for k in a_supprimer:
                del _DEDUP_CACHE[k]

        # Récap périodique
        if maintenant - _DERNIER_RECAP > LOG_RECAP_INTERVAL_SEC and _SUPPRIMEES:
            _envoyer_recap_supprimees()
            _DERNIER_RECAP = maintenant
            _SUPPRIMEES.clear()

    return True


from core.securite import nettoyer_html


def _formater_contexte(user_context: Optional[Dict], api_context: Optional[Dict],
                       db_context: Optional[Dict], handler: Optional[str],
                       extra: Optional[Dict]) -> str:
    """Formate les blocs de contexte en HTML Telegram."""
    blocs = []

    if user_context:
        lignes = []
        if user_context.get("user_id"):
            lignes.append(f"   • ID : <code>{nettoyer_html(user_context['user_id'])}</code>")
        if user_context.get("user_name"):
            lignes.append(f"   • Nom : {nettoyer_html(user_context['user_name'])}")
        if user_context.get("username"):
            lignes.append(f"   • Username : @{nettoyer_html(user_context['username'])}")
        if user_context.get("chat_id"):
            lignes.append(f"   • Chat ID : <code>{nettoyer_html(user_context['chat_id'])}</code>")
        if user_context.get("langue"):
            lignes.append(f"   • Langue : {nettoyer_html(user_context['langue'])}")
        if user_context.get("statut"):
            lignes.append(f"   • Statut : {nettoyer_html(user_context['statut'])}")
        if user_context.get("message_text"):
            msg = str(user_context["message_text"])[:200]
            lignes.append(f"   • Message : <i>\"{nettoyer_html(msg)}\"</i>")
        if user_context.get("command"):
            lignes.append(f"   • Commande : {nettoyer_html(user_context['command'])}")
        if lignes:
            blocs.append("👤 <b>Utilisateur</b>\n" + "\n".join(lignes))

    if api_context:
        lignes = []
        if api_context.get("source"):
            lignes.append(f"   • Source : <b>{nettoyer_html(api_context['source'])}</b>")
        if api_context.get("url"):
            url = str(api_context["url"])[:300]
            lignes.append(f"   • URL : <code>{nettoyer_html(url)}</code>")
        if api_context.get("http_status"):
            lignes.append(f"   • Statut HTTP : <code>{nettoyer_html(api_context['http_status'])}</code>")
        if api_context.get("http_body"):
            body = str(api_context["http_body"])[:200]
            lignes.append(f"   • Réponse : <code>{nettoyer_html(body)}</code>")
        if api_context.get("attempt"):
            lignes.append(f"   • Tentative : {nettoyer_html(api_context['attempt'])}")
        if api_context.get("duration_ms"):
            lignes.append(f"   • Durée : {api_context['duration_ms']} ms")
        if lignes:
            blocs.append("🌐 <b>API externe</b>\n" + "\n".join(lignes))

    if db_context:
        lignes = []
        if db_context.get("query"):
            query = str(db_context["query"])[:300]
            lignes.append(f"   • Requête : <code>{nettoyer_html(query)}</code>")
        if db_context.get("table"):
            lignes.append(f"   • Table : {nettoyer_html(db_context['table'])}")
        if db_context.get("params"):
            params = str(db_context["params"])[:200]
            lignes.append(f"   • Paramètres : <code>{nettoyer_html(params)}</code>")
        if lignes:
            blocs.append("🗄️ <b>Base de données</b>\n" + "\n".join(lignes))

    if handler:
        blocs.append(f"🔧 <b>Handler</b> : <code>{nettoyer_html(handler)}</code>")

    if extra:
        lignes = []
        for k, v in extra.items():
            valeur = str(v)[:200]
            lignes.append(f"   • {nettoyer_html(k)} : {nettoyer_html(valeur)}")
        if lignes:
            blocs.append("📋 <b>Détails</b>\n" + "\n".join(lignes))

    return "\n\n".join(blocs)


def _get_metriques() -> str:
    """Retourne les métriques d'environnement (uptime, mémoire)."""
    lignes = []
    uptime = time.time() - _START_TIME
    jours = int(uptime // 86400)
    heures = int((uptime % 86400) // 3600)
    minutes = int((uptime % 3600) // 60)
    lignes.append(f"   • Uptime : {jours}j {heures}h {minutes}min")

    try:
        import resource
        mem_mo = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        lignes.append(f"   • Mémoire : {mem_mo:.0f} Mo")
    except ImportError:
        pass

    lignes.append(f"   • Python : {sys.version.split()[0]}")
    lignes.append(f"   • PID : {os.getpid()}")

    return "⚙️ <b>Environnement</b>\n" + "\n".join(lignes)


def _get_handler_depuis_stack() -> Optional[str]:
    """Détecte le handler (fonction appelante) depuis la stack."""
    try:
        stack = traceback.extract_stack()
        # On remonte la stack pour trouver un handler Telegram
        for frame in reversed(stack[:-3]):  # on saute les frames de logs
            nom = frame.name
            if nom.startswith("handle_") or nom.startswith("cmd_") or nom.startswith("traiter_"):
                return nom
    except Exception:
        pass
    return None


def _envoyer_telegram_sync(texte: str) -> bool:
    """Envoie un message à l'admin (synchrone, avec gestion d'erreur)."""
    if not TOKEN:
        print("⚠️ TOKEN manquant : impossible d'envoyer l'alerte Telegram.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_ID,
            "text": texte[:4000],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code != 200:
            # Ne PAS logguer via log_error (récursion infinie)
            print(f"⚠️ Telegram a refusé le message ({res.status_code}) : {res.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Impossible d'envoyer l'alerte à l'admin : {e}")
        return False


def _envoyer_async(texte: str):
    """Envoie en arrière-plan via un thread daemon."""
    def _worker():
        try:
            _envoyer_telegram_sync(texte)
        except Exception as e:
            print(f"⚠️ Erreur dans _envoyer_async : {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _envoyer_recap_supprimees():
    """Envoie un récapitulatif des erreurs supprimées par anti-flood."""
    if not _SUPPRIMEES:
        return
    lignes = ["📊 <b>RÉCAP ANTI-FLOOD</b>\n"]
    lignes.append(f"Fenêtre : {LOG_RECAP_INTERVAL_SEC // 60} min\n")
    for hash_cle, count in _SUPPRIMEES.items():
        lignes.append(f"   • <code>{hash_cle}</code> : {count} occurrence(s) supprimée(s)")
    texte = "\n".join(lignes)
    _envoyer_async(texte)


# =========================================================
# API PUBLIQUE
# =========================================================
def log_info(message: str, module: str = "BOT",
             user_context: Optional[Dict] = None,
             api_context: Optional[Dict] = None,
             db_context: Optional[Dict] = None,
             handler: Optional[str] = None,
             extra: Optional[Dict] = None):
    """Log une information normale (print seulement, pas de Telegram)."""
    prefixe = f"[{module}]"
    if handler:
        prefixe += f"[{handler}]"
    if user_context and user_context.get("user_id"):
        prefixe += f"[user:{user_context['user_id']}]"
    print(f"{prefixe} ℹ️ {message}")


def log_warning(message: str, module: str = "BOT",
                user_context: Optional[Dict] = None,
                api_context: Optional[Dict] = None,
                db_context: Optional[Dict] = None,
                handler: Optional[str] = None,
                exception: Optional[Exception] = None,
                extra: Optional[Dict] = None):
    """Log un avertissement + envoi Telegram (avec anti-flood)."""
    prefixe = f"[{module}]"
    if handler:
        prefixe += f"[{handler}]"
    print(f"{prefixe} ⚠️ {message}")

    hash_cle = _hash_erreur(module, message)
    if not _doit_envoyer(hash_cle):
        return

    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y à %H:%M:%S")
    handler_final = handler or _get_handler_depuis_stack() or "N/A"

    blocs = [
        f"⚠️ <b>AVERTISSEMENT</b>\n",
        f"📅 {date_str} (Kinshasa)",
        f"🆔 <code>{hash_cle}</code>",
        f"📌 Module : <b>{nettoyer_html(module)}</b>",
    ]

    if handler_final != "N/A":
        blocs.append(f"🔧 Handler : <code>{nettoyer_html(handler_final)}</code>")

    ctx = _formater_contexte(user_context, api_context, db_context, None, extra)
    if ctx:
        blocs.append(ctx)

    blocs.append(f"\n📝 <b>Message</b> :\n{nettoyer_html(message)}")

    if exception:
        trace = traceback.format_exc()
        if trace and "NoneType: None" not in trace:
            blocs.append(f"\n🔍 <b>Trace</b> :\n<pre>{nettoyer_html(trace[:2500])}</pre>")

    texte = "\n".join(blocs)
    _envoyer_async(texte)


def log_error(message: str, module: str = "BOT",
              user_context: Optional[Dict] = None,
              api_context: Optional[Dict] = None,
              db_context: Optional[Dict] = None,
              handler: Optional[str] = None,
              exception: Optional[Exception] = None,
              extra: Optional[Dict] = None):
    """Log une erreur + envoi Telegram détaillé (avec anti-flood)."""
    prefixe = f"[{module}]"
    if handler:
        prefixe += f"[{handler}]"
    print(f"{prefixe} ❌ {message}")

    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"{prefixe} 🔥 TRACEBACK:\n{trace}")

    hash_cle = _hash_erreur(module, message)
    if not _doit_envoyer(hash_cle):
        return

    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y à %H:%M:%S")
    handler_final = handler or _get_handler_depuis_stack() or "N/A"

    blocs = [
        f"🚨 <b>ERREUR DÉTECTÉE</b>\n",
        f"📅 {date_str} (Kinshasa)",
        f"🆔 <code>{hash_cle}</code>",
        f"📌 Module : <b>{nettoyer_html(module)}</b>",
    ]

    if handler_final != "N/A":
        blocs.append(f"🔧 Handler : <code>{nettoyer_html(handler_final)}</code>")

    ctx = _formater_contexte(user_context, api_context, db_context, None, extra)
    if ctx:
        blocs.append(ctx)

    blocs.append(f"\n📝 <b>Message</b> :\n{nettoyer_html(message)}")

    if trace and "NoneType: None" not in trace:
        blocs.append(f"\n🔍 <b>Trace</b> :\n<pre>{nettoyer_html(trace[:2500])}</pre>")

    blocs.append("\n" + _get_metriques())

    texte = "\n".join(blocs)
    _envoyer_async(texte)


def log_critical(message: str, module: str = "BOT",
                 user_context: Optional[Dict] = None,
                 api_context: Optional[Dict] = None,
                 db_context: Optional[Dict] = None,
                 handler: Optional[str] = None,
                 exception: Optional[Exception] = None,
                 extra: Optional[Dict] = None):
    """Log une erreur critique (TOUJOURS envoyé, 3 fois, même en flood)."""
    prefixe = f"[{module}]"
    if handler:
        prefixe += f"[{handler}]"
    print(f"{prefixe} 🚨 CRITIQUE : {message}")

    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"{prefixe} 🔥 TRACEBACK:\n{trace}")

    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y à %H:%M:%S")
    handler_final = handler or _get_handler_depuis_stack() or "N/A"

    blocs = [
        f"🚨🚨 <b>ERREUR CRITIQUE</b> 🚨🚨\n",
        f"📅 {date_str} (Kinshasa)",
        f"📌 Module : <b>{nettoyer_html(module)}</b>",
    ]

    if handler_final != "N/A":
        blocs.append(f"🔧 Handler : <code>{nettoyer_html(handler_final)}</code>")

    ctx = _formater_contexte(user_context, api_context, db_context, None, extra)
    if ctx:
        blocs.append(ctx)

    blocs.append(f"\n📝 <b>Message</b> :\n{nettoyer_html(message)}")

    if trace and "NoneType: None" not in trace:
        blocs.append(f"\n🔍 <b>Trace</b> :\n<pre>{nettoyer_html(trace[:2500])}</pre>")

    blocs.append("\n" + _get_metriques())

    texte = "\n".join(blocs)

    # Envoi garanti (3 fois, espacé de 2s)
    for i in range(3):
        _envoyer_async(texte)
        time.sleep(2)


def log_canal_action(action: str, succes: bool, details: str = "",
                     user_context: Optional[Dict] = None):
    """Log spécifique pour les actions sur le canal."""
    statut = "✅" if succes else "❌"
    print(f"[CANAL] {statut} {action} - {details}")
    if not succes:
        log_error(
            message=f"Échec action canal : {action} - {details}",
            module="CANAL",
            user_context=user_context,
        )
