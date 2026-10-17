import telebot

def menu_principal_admin():
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
        telebot.types.InlineKeyboardButton("❌ Fermer", callback_data="admin_close")
    )
    return markup

def menu_premium():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("➕ Ajouter Premium", callback_data="admin_add_premium"),
        telebot.types.InlineKeyboardButton("➖ Retirer Premium", callback_data="admin_remove_premium"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup

def menu_codes():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Gen 10 jours", callback_data="admin_gen_10"),
        telebot.types.InlineKeyboardButton("Gen 30 jours", callback_data="admin_gen_30"),
        telebot.types.InlineKeyboardButton("Gen 90 jours", callback_data="admin_gen_90"),
        telebot.types.InlineKeyboardButton("Gen custom", callback_data="admin_gen_custom"),
        telebot.types.InlineKeyboardButton("👁️ Voir codes dispo", callback_data="admin_voir_codes"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup

def menu_parametres():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Heure notifs", callback_data="param_notif_heure"),
        telebot.types.InlineKeyboardButton("Limite Free", callback_data="param_limite_free"),
        telebot.types.InlineKeyboardButton("Prix Stars", callback_data="param_prix_stars"),
        telebot.types.InlineKeyboardButton("Message accueil", callback_data="param_message_accueil"),
        telebot.types.InlineKeyboardButton("Mode maintenance", callback_data="param_mode_maintenance"),
        telebot.types.InlineKeyboardButton("👁️ Voir parametres", callback_data="admin_voir_params"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup

def menu_bdd():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Taille BDD", callback_data="admin_taille_bdd"),
        telebot.types.InlineKeyboardButton("Detail tables", callback_data="admin_detail_tables"),
        telebot.types.InlineKeyboardButton("🧹 Nettoyer", callback_data="admin_nettoyer"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup
