import traceback
import threading
import requests
from datetime import datetime

# ⚠️ On importe config ici pour éviter les imports circulaires
try:
    from config import TOKEN
except ImportError:
    TOKEN = None

# ⚠️ Identifiant de l'administrateur principal
ADMIN_ID = 8653408729


def _envoyer_telegram(message_texte):
    """Envoie un message brut à l'admin via l'API Telegram."""
    if not TOKEN:
        print("⚠️ TOKEN manquant, impossible d'envoyer l'alerte Telegram.")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_ID,
            "text": message_texte[:4000],  # Tronqué pour respecter la limite Telegram
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ Impossible d'envoyer l'alerte à l'admin : {e}")


def _executer_en_arriere_plan(fonction, *args, **kwargs):
    """Lance une fonction dans un thread pour ne pas bloquer le bot."""
    t = threading.Thread(target=fonction, args=args, kwargs=kwargs, daemon=True)
    t.start()


def log_info(message, module="BOT"):
    """Log une information normale."""
    print(f"[{module}] ℹ️ {message}")


def log_warning(message, module="BOT"):
    """
    Log un avertissement.
    ⚠️ Par défaut, on notifie quand même l'admin (car on veut zéro surprise).
    """
    print(f"[{module}] ⚠️ {message}")
    
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    message_secu = message.replace("<", "&lt;").replace(">", "&gt;")
    texte = (
        f"⚠️ <b>AVERTISSEMENT</b>\n\n"
        f"📅 {date_str}\n"
        f"📌 Module : <b>{module}</b>\n\n"
        f"📝 {message_secu}"
    )
    _executer_en_arriere_plan(_envoyer_telegram, texte)


def log_error(message, module="BOT", exception=None):
    """
    Log une erreur avec la trace complète.
    Envoie TOUJOURS l'erreur à l'admin via Telegram.
    """
    print(f"[{module}] ❌ {message}")
    
    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"[{module}] 🔥 TRACEBACK:\n{trace}")
    
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    message_secu = message.replace("<", "&lt;").replace(">", "&gt;")
    trace_secu = trace.replace("<", "&lt;").replace(">", "&gt;") if trace else ""
    
    texte = (
        f"🚨 <b>ERREUR DÉTECTÉE</b>\n\n"
        f"📅 {date_str}\n"
        f"📌 Module : <b>{module}</b>\n\n"
        f"📝 <b>Message :</b>\n{message_secu}\n"
    )
    if trace_secu:
        texte += f"\n🔍 <b>Trace :</b>\n<pre>{trace_secu[:3000]}</pre>"
    
    _executer_en_arriere_plan(_envoyer_telegram, texte)


def log_critical(message, module="BOT", exception=None):
    """
    Log une erreur critique (bot peut s'arrêter).
    Envoie TOUJOURS avec un préfixe visuel fort.
    """
    print(f"[{module}] 🚨 CRITIQUE : {message}")
    
    trace = ""
    if exception:
        trace = traceback.format_exc()
        print(f"[{module}] 🔥 TRACEBACK:\n{trace}")
    
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    message_secu = message.replace("<", "&lt;").replace(">", "&gt;")
    trace_secu = trace.replace("<", "&lt;").replace(">", "&gt;") if trace else ""
    
    texte = (
        f"🚨🚨 <b>ERREUR CRITIQUE</b> 🚨🚨\n\n"
        f"📅 {date_str}\n"
        f"📌 Module : <b>{module}</b>\n\n"
        f"📝 <b>Message :</b>\n{message_secu}\n"
    )
    if trace_secu:
        texte += f"\n🔍 <b>Trace :</b>\n<pre>{trace_secu[:3000]}</pre>"
    
    _executer_en_arriere_plan(_envoyer_telegram, texte)


def log_canal_action(action, succes, details=""):
    """Log spécifique pour les actions sur le canal."""
    statut = "✅" if succes else "❌"
    print(f"[CANAL] {statut} {action} - {details}")
    if not succes:
        log_error(f"Échec action canal : {action} - {details}", "CANAL")
