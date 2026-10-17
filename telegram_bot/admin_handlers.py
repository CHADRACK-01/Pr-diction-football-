import time
import telebot
from datetime import datetime, timedelta

from users import (
    est_administrateur, get_stats_globales, get_liste_utilisateurs,
    ajouter_admin, retirer_admin, get_tous_admins,
    bannir_user, debannir_user, get_liste_bannis,
    log_admin, get_logs_admin,
    get_parametre, set_parametre, get_tous_parametres,
    set_premium, get_tous_utilisateurs,
    get_user_info,
    get_demandes_en_attente, compter_demandes_en_attente,
    get_codes_disponibles, generer_lot_codes,
    compter_codes_disponibles,
    get_taille_base, get_detail_tables,
    nettoyer_logs_anciens, nettoyer_paiements_anciens,
    ajouter_jours_premium
)
from users.db import get_connection
from core.broadcast_manager import lancer_broadcast_async
from config import CANAL_ID

# ⚠️ Import du module de test
from telegram_bot.admin_tests import enregistrer_tests_handlers, _menu_test_canal

ADMIN_SESSIONS = {}

def _retirer_premium(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE utilisateurs SET status = 'free', date_expiration = NULL WHERE user_id = %s", (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur _retirer_premium : {e}")
        return False

# =========================================================
# MENUS INLINE
# =========================================================
def _menu_principal_admin():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("👥 Utilisateurs", callback_data="admin_users"),
        telebot.types.InlineKeyboardButton("💳 Paiements", callback_data="admin_payments"),
        telebot.types.InlineKeyboardButton("🎟️ Codes Premium", callback_data="admin_codes"),
        telebot.types.InlineKeyboardButton("🗄️ Base de données", callback_data="admin_bdd"),
        telebot.types.InlineKeyboardButton("👑 Admins", callback_data="admin_admins"),
        telebot.types.InlineKeyboardButton("⚙️ Paramètres", callback_data="admin_params"),
        telebot.types.InlineKeyboardButton("📝 Logs", callback_data="admin_logs"),
        telebot.types.InlineKeyboardButton("🚫 Bannis", callback_data="admin_bannis"),
        telebot.types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        telebot.types.InlineKeyboardButton("💎 Premium", callback_data="admin_premium"),
        telebot.types.InlineKeyboardButton("🧪 Tests Canal", callback_data="admin_test_menu"), # Lien vers le module externe
        telebot.types.InlineKeyboardButton("❌ Fermer", callback_data="admin_close")
    )
    return markup

def _menu_premium():
    # ... (inchangé) ...

def _menu_codes():
    # ... (inchangé) ...

def _menu_parametres():
    # ... (inchangé) ...

def _menu_bdd():
    # ... (inchangé) ...


def enregistrer_admin_handlers(bot):
    # ⚠️ On enregistre le module de test
    enregistrer_tests_handlers(bot)

    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            return
        bot.send_message(message.chat.id, "🎛️ **PANNEAU ADMIN**\n\nChoisis une action :", reply_markup=_menu_principal_admin(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
    def open_admin_panel_callback(call):
        # ... (inchangé) ...

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("admin_", "param_", "bcast_")))
    def handle_admin_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return
            
        data = call.data
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        if data == "admin_back":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("🎛️ **PANNEAU ADMIN**\n\nChoisis une action :", call.message.chat.id, call.message.message_id, reply_markup=_menu_principal_admin(), parse_mode="Markdown")
        elif data == "admin_close":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        elif data == "admin_premium":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("💎 **GESTION PREMIUM**", call.message.chat.id, call.message.message_id, reply_markup=_menu_premium(), parse_mode="Markdown")
        elif data == "admin_codes":
            ADMIN_SESSIONS.pop(user_id, None)
            dispo = compter_codes_disponibles()
            bot.edit_message_text(f"🎟️ **CODES PREMIUM**\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=_menu_codes(), parse_mode="Markdown")
        elif data == "admin_bdd":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("🗄️ **BASE DE DONNÉES**", call.message.chat.id, call.message.message_id, reply_markup=_menu_bdd(), parse_mode="Markdown")
        elif data == "admin_params":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("⚙️ **PARAMÈTRES**", call.message.chat.id, call.message.message_id, reply_markup=_menu_parametres(), parse_mode="Markdown")
        elif data == "admin_stats":
            stats = get_stats_globales()
            texte = f"📊 **STATISTIQUES**\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
        elif data == "admin_users":
            # ... (inchangé) ...
        elif data == "admin_payments":
            # ... (inchangé) ...
        elif data == "admin_taille_bdd":
            # ... (inchangé) ...
        elif data == "admin_detail_tables":
            # ... (inchangé) ...
        elif data == "admin_nettoyer":
            # ... (inchangé) ...
        elif data == "admin_admins":
            # ... (inchangé) ...
        elif data == "admin_logs":
            # ... (inchangé) ...
        elif data == "admin_bannis":
            # ... (inchangé) ...
        elif data == "admin_broadcast":
            # ... (inchangé) ...
        elif data.startswith("bcast_"):
            # ... (inchangé) ...
        elif data == "admin_add_premium":
            # ... (inchangé) ...
        elif data == "admin_remove_premium":
            # ... (inchangé) ...
        elif data in ["admin_gen_10", "admin_gen_30", "admin_gen_90"]:
            # ... (inchangé) ...
        elif data == "admin_gen_custom":
            # ... (inchangé) ...
        elif data == "admin_voir_codes":
            # ... (inchangé) ...
        elif data.startswith("param_"):
            # ... (inchangé) ...
        elif data == "admin_voir_params":
            # ... (inchangé) ...

    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        # ... (inchangé) ...

    def _traiter_gen_custom(message):
        # ... (inchangé) ...
    def _traiter_param(message):
        # ... (inchangé) ...
    def _traiter_broadcast(message):
        # ... (inchangé) ...
    def _traiter_add_premium(message):
        # ... (inchangé) ...
    def _traiter_remove_premium(message):
        # ... (inchangé) ... cc
