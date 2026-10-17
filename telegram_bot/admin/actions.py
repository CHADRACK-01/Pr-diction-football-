import telebot
from datetime import datetime, timedelta

from users import (
    get_stats_globales, get_liste_utilisateurs, get_tous_admins,
    log_admin, get_logs_admin, get_parametre, set_parametre,
    get_tous_parametres, set_premium, get_tous_utilisateurs,
    get_demandes_en_attente, get_codes_disponibles, generer_lot_codes,
    compter_codes_disponibles, get_taille_base, get_detail_tables,
    nettoyer_logs_anciens, nettoyer_paiements_anciens,
    ajouter_jours_premium, get_liste_bannis
)
from users.db import get_connection
from core.broadcast_manager import lancer_broadcast_async
from core.utils.logs import log_info, log_error
from telegram_bot.admin.menus import (
    menu_premium, menu_codes, menu_bdd, menu_parametres
)

ADMIN_SESSIONS = {}

def _retirer_premium(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE utilisateurs SET status = 'free', date_expiration = NULL WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Erreur _retirer_premium : {e}", "ADMIN")
        return False


def executer_action(bot, call, data, user_id):
    """Exécute l'action correspondant au bouton cliqué avec des logs de debug."""
    
    log_info(f"EXECUTION ACTION : '{data}' demandée par {user_id}", "ADMIN")

    # --- STATS ---
    if data == "admin_stats":
        stats = get_stats_globales()
        texte = f"📊 STATISTIQUES\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}"
        bot.send_message(call.message.chat.id, texte)
    
    # --- UTILISATEURS ---
    elif data == "admin_users":
        users = get_liste_utilisateurs(limite=20)
        texte = "👥 UTILISATEURS\n\n"
        for u in users:
            statut = "💎" if u['status'] == 'premium' else "🆓"
            texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
        bot.send_message(call.message.chat.id, texte)

    # --- PAIEMENTS ---
    elif data == "admin_payments":
        demandes = get_demandes_en_attente(limite=10)
        if not demandes:
            bot.send_message(call.message.chat.id, "Aucun paiement en attente.")
            return
        for d in demandes:
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}")
            )
            bot.send_photo(call.message.chat.id, d['preuve_photo_id'], caption=f"#{d['id']} - User {d['user_id']}\nMontant: {d['montant']} CDF", reply_markup=markup)

    # --- BDD ---
    elif data == "admin_taille_bdd":
        bot.send_message(call.message.chat.id, f"🗄️ Taille totale : {get_taille_base()}")
    
    elif data == "admin_detail_tables":
        tables = get_detail_tables()
        if not tables:
            bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les détails.")
            return
        texte = "🗄️ DETAIL PAR TABLE\n\n"
        for t in tables[:10]:
            texte += f"• {t['table_name']} : {t['size']}\n"
        bot.send_message(call.message.chat.id, texte)

    elif data == "admin_nettoyer":
        logs = nettoyer_logs_anciens(jours=30)
        paiements = nettoyer_paiements_anciens(jours=90)
        bot.send_message(call.message.chat.id, f"🧹 Nettoyage terminé\n• {logs} log(s)\n• {paiements} paiement(s)")

    # --- ADMINS ---
    elif data == "admin_admins":
        admins = get_tous_admins()
        texte = "👑 ADMINS\n\nPrincipal : 8653408729\n\n"
        for a in admins:
            texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
        bot.send_message(call.message.chat.id, texte)

    # --- LOGS ---
    elif data == "admin_logs":
        logs = get_logs_admin(limite=15)
        texte = "📝 LOGS ADMIN\n\n"
        for log in logs:
            texte += f"- {log['action']} (Par {log['admin_id']})\n"
        bot.send_message(call.message.chat.id, texte)

    # --- BANNIS ---
    elif data == "admin_bannis":
        bannis = get_liste_bannis()
        texte = "🚫 BANNIS\n\n"
        for b in bannis:
            texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
        bot.send_message(call.message.chat.id, texte)

    # --- PARAMÈTRES ---
    elif data == "admin_params_menu":
        bot.edit_message_text("⚙️ PARAMÈTRES\n\nChoisis un paramètre :", call.message.chat.id, call.message.message_id, reply_markup=menu_parametres())

    elif data.startswith("param_"):
        cle = data.replace("param_", "")
        ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: 
            pass
        msg = bot.send_message(call.message.chat.id, f"Envoie la nouvelle valeur pour {cle} :\n\n/annuler pour annuler.")
        bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m, ADMIN_SESSIONS))

    elif data == "admin_voir_params":
        params = get_tous_parametres()
        texte = "⚙️ PARAMETRES ACTUELS\n\n"
        for p in params:
            texte += f"- {p['cle']} = {p['valeur']}\n"
        bot.send_message(call.message.chat.id, texte)

    # --- PREMIUM ---
    elif data == "admin_premium":
        ADMIN_SESSIONS.pop(user_id, None)
        bot.edit_message_text("💎 GESTION PREMIUM", call.message.chat.id, call.message.message_id, reply_markup=menu_premium())
    
    elif data == "admin_add_premium":
        ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
        msg = bot.send_message(call.message.chat.id, "Format : ID jours\nExemple : 123456789 30")
        bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m, ADMIN_SESSIONS))

    elif data == "admin_remove_premium":
        ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
        msg = bot.send_message(call.message.chat.id, "Envoie l'ID utilisateur :")
        bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m, ADMIN_SESSIONS))

    # --- CODES ---
    elif data == "admin_codes":
        ADMIN_SESSIONS.pop(user_id, None)
        dispo = compter_codes_disponibles()
        bot.edit_message_text(f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=menu_codes())

    elif data in ["admin_gen_10", "admin_gen_30", "admin_gen_90"]:
        jours = int(data.split("_")[-1])
        codes = generer_lot_codes(jours, 10)
        log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
        texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
        for c in codes:
            texte += f"{c}\n"
        bot.send_message(call.message.chat.id, texte)

    elif data == "admin_gen_custom":
        ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
        msg = bot.send_message(call.message.chat.id, "Envoie : jours quantite\nExemple : 30 20")
        bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m, ADMIN_SESSIONS))

    elif data == "admin_voir_codes":
        codes = get_codes_disponibles(limite=30)
        if not codes:
            bot.send_message(call.message.chat.id, "Aucun code disponible.")
            return
        texte = f"🎟️ CODES DISPO\n\n"
        for c in codes:
            texte += f"{c['code']} ({c['jours']}j)\n"
        bot.send_message(call.message.chat.id, texte)

    # --- BROADCAST ---
    elif data == "admin_broadcast":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("📱 Utilisateurs + 📢 Canal", callback_data="bcast_all"),
            telebot.types.InlineKeyboardButton("📱 Utilisateurs uniquement", callback_data="bcast_users"),
            telebot.types.InlineKeyboardButton("📢 Canal uniquement", callback_data="bcast_canal")
        )
        bot.send_message(call.message.chat.id, "Où veux-tu envoyer l'annonce ?", reply_markup=markup)

    elif data.startswith("bcast_"):
        cible = data.split("_")[1]
        ADMIN_SESSIONS[user_id] = {"action": "broadcast", "cible": cible}
        msg = bot.send_message(call.message.chat.id, "Envoie le message à diffuser :\n\n/annuler pour annuler.")
        bot.register_next_step_handler(msg, lambda m: _traiter_broadcast(bot, m, ADMIN_SESSIONS))

    # --- BDD (raccourci) ---
    elif data == "admin_bdd":
        ADMIN_SESSIONS.pop(user_id, None)
        bot.edit_message_text("🗄️ BASE DE DONNÉES", call.message.chat.id, call.message.message_id, reply_markup=menu_bdd())

    else:
        log_info(f"Aucune action trouvée pour '{data}'", "ADMIN")
        bot.send_message(call.message.chat.id, f"⚠️ Action '{data}' non reconnue.")


# =========================================================
# FONCTIONS DE TRAITEMENT
# =========================================================
def _traiter_param(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annule.")
        return

    session = sessions.get(user_id, {})
    cle = session.get("cle")

    if not cle:
        bot.reply_to(message, "Erreur session.")
        return

    if set_parametre(cle, texte):
        log_admin(user_id, "set_param", f"{cle} = {texte}")
        bot.reply_to(message, f"✅ {cle} a été mis à jour sur : {texte}")

    sessions.pop(user_id, None)


def _traiter_gen_custom(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annule.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "Format invalide.")
        return

    jours = int(parts[0])
    quantite = int(parts[1])

    if quantite > 100:
        bot.reply_to(message, "Maximum 100 codes.")
        return

    codes = generer_lot_codes(jours, quantite)
    log_admin(user_id, "gen_codes_custom", f"{quantite} codes de {jours}j")

    texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
    for c in codes:
        texte += f"{c}\n"
    bot.reply_to(message, texte)
    sessions.pop(user_id, None)


def _traiter_broadcast(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annule.")
        return

    if not texte:
        bot.reply_to(message, "Message vide.")
        return

    session = sessions.get(user_id, {})
    cible = session.get("cible", "users")

    users = get_tous_utilisateurs() if cible in ["users", "all"] else []
    admins = get_tous_admins()
    envoyer_canal = cible in ["canal", "all"]

    bot.reply_to(message, "🚀 Diffusion lancée en arrière-plan. Tu recevras un récapitulatif à la fin.")
    lancer_broadcast_async(bot, users, texte, admins, canal=envoyer_canal)
    log_admin(user_id, "broadcast", f"Cible: {cible}")
    sessions.pop(user_id, None)


def _traiter_add_premium(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annule.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "Format invalide. Usage : ID jours")
        return

    target = int(parts[0])
    jours = int(parts[1])
    expiration = (datetime.now() + timedelta(days=jours)).strftime("%Y-%m-%d %H:%M")

    if set_premium(target, expiration):
        log_admin(user_id, "add_premium", f"ID: {target} - {jours}j")
        bot.reply_to(message, f"✅ Utilisateur {target} PREMIUM pour {jours} jours\nExpire : {expiration}")
        try:
            bot.send_message(target, f"💎 Ton compte a été passé en PREMIUM !\n\nDurée : {jours} jours\nExpire : {expiration}")
        except Exception: 
            pass
    else:
        bot.reply_to(message, "Utilisateur introuvable.")

    sessions.pop(user_id, None)


def _traiter_remove_premium(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annule.")
        return

    if not texte.isdigit():
        bot.reply_to(message, "ID invalide.")
        return

    target = int(texte)

    if _retirer_premium(target):
        log_admin(user_id, "remove_premium", f"ID: {target}")
        bot.reply_to(message, f"✅ Utilisateur {target} est repassé en FREE.")
        try:
            bot.send_message(target, "Ton abonnement Premium a été retiré.")
        except Exception: 
            pass
    else:
        bot.reply_to(message, "Utilisateur introuvable.")

    sessions.pop(user_id, None)
