import telebot

# --- MENUS EN BAS (ReplyKeyboardMarkup) ---

def menu_principal_admin_bas():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("📊 Stats"),
        telebot.types.KeyboardButton("👥 Utilisateurs"),
        telebot.types.KeyboardButton("💳 Paiements"),
        telebot.types.KeyboardButton("🎟️ Codes Premium"),
        telebot.types.KeyboardButton("🗄️ Base de données"),
        telebot.types.KeyboardButton("👑 Admins"),
        telebot.types.KeyboardButton("⚙️ Paramètres"),
        telebot.types.KeyboardButton("📝 Logs"),
        telebot.types.KeyboardButton("🚫 Bannis"),
        telebot.types.KeyboardButton("📢 Broadcast"),
        telebot.types.KeyboardButton("💎 Premium"),
        telebot.types.KeyboardButton("🔙 Quitter Admin")
    )
    return markup

def menu_premium_bas():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("➕ Ajouter Premium"),
        telebot.types.KeyboardButton("➖ Retirer Premium"),
        telebot.types.KeyboardButton("🔙 Retour Admin")
    )
    return markup

def menu_codes_bas():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Gen 10 jours"),
        telebot.types.KeyboardButton("Gen 30 jours"),
        telebot.types.KeyboardButton("Gen 90 jours"),
        telebot.types.KeyboardButton("Gen custom"),
        telebot.types.KeyboardButton("👁️ Voir codes dispo"),
        telebot.types.KeyboardButton("🔙 Retour Admin")
    )
    return markup

def menu_parametres_bas():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Heure notifs"),
        telebot.types.KeyboardButton("Limite Free"),
        telebot.types.KeyboardButton("Prix Stars"),
        telebot.types.KeyboardButton("Message accueil"),
        telebot.types.KeyboardButton("Mode maintenance"),
        telebot.types.KeyboardButton("👁️ Voir parametres"),
        telebot.types.KeyboardButton("🔙 Retour Admin")
    )
    return markup

def menu_bdd_bas():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Taille BDD"),
        telebot.types.KeyboardButton("Detail tables"),
        telebot.types.KeyboardButton("🧹 Nettoyer"),
        telebot.types.KeyboardButton("🔙 Retour Admin")
    )
    return markup

# ... (On garde aussi les menus Inline pour les tests éventuels, mais on ne les utilise plus)
