import telebot
from datetime import datetime, timedelta
from users import (
    get_stats_globales, get_liste_utilisateurs, get_tous_admins,
    bannir_user, debannir_user, get_liste_bannis,
    log_admin, get_logs_admin,
    get_parametre, set_parametre, get_tous_parametres,
    set_premium, get_tous_utilisateurs,
    get_user_info, get_demandes_en_attente, compter_demandes_en_attente,
    get_codes_disponibles, generer_lot_codes, compter_codes_disponibles,
    get_taille_base, get_detail_tables,
    nettoyer_logs_anciens, nettoyer_paiements_anciens
)
from users.db import get_connection
from core.broadcast_manager import lancer_broadcast_async
from config import CANAL_ID

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

def executer_action(bot, call, data, user_id):
    """Exécute l'action correspondant au bouton cliqué."""
    if data == "admin_stats":
        stats = get_stats_globales()
        texte = f"📊 **STATISTIQUES**\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}\n\nNouveaux (7j) : {stats.get('nouveaux_7j', 0)}\nBannis : {stats.get('bannis', 0)}"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
    
    elif data == "admin_users":
        users = get_liste_utilisateurs(limite=20)
        texte = "👥 **UTILISATEURS**\n\n"
        for u in users:
            statut = "💎" if u['status'] == 'premium' else "🆓"
            texte += f"{statut} {u['first_name'] or '?'} : `{u['user_id']}`\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

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
            bot.send_photo(call.message.chat.id, d['preuve_photo_id'], caption=f"#{d['id']} - User `{d['user_id']}`\nMontant: {d['montant']} CDF", reply_markup=markup, parse_mode="Markdown")

    elif data == "admin_taille_bdd":
        bot.send_message(call.message.chat.id, f"🗄️ Taille totale : **{get_taille_base()}**", parse_mode="Markdown")
    
    elif data == "admin_detail_tables":
        tables = get_detail_tables()
        if not tables:
            bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les détails.")
            return
        texte = "🗄️ **DETAIL PAR TABLE**\n\n"
        for t in tables[:10]:
            texte += f"• {t['table_name']} : {t['size']}\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

    elif data == "admin_nettoyer":
        logs = nettoyer_logs_anciens(jours=30)
        paiements = nettoyer_paiements_anciens(jours=90)
        bot.send_message(call.message.chat.id, f"🧹 Nettoyage terminé\n\n• {logs} log(s)\n• {paiements} paiement(s)")

    elif data == "admin_admins":
        admins = get_tous_admins()
        texte = "👑 **ADMINS**\n\nPrincipal : `8653408729`\n\n"
        for a in admins:
            texte += f"- `{a['user_id']}` : {a['nom'] or 'Sans nom'}\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

    elif data == "admin_logs":
        logs = get_logs_admin(limite=15)
        texte = "📝 **LOGS ADMIN**\n\n"
        for log in logs:
            texte += f"- {log['action']}\n  Par : `{log['admin_id']}`\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

    elif data == "admin_bannis":
        bannis = get_liste_bannis()
        texte = "🚫 **BANNIS**\n\n"
        for b in bannis:
            texte += f"- `{b['user_id']}` : {b['raison'] or 'Sans raison'}\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

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
        from telegram_bot.admin_handlers import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {"action": "broadcast", "cible": cible}
        msg = bot.send_message(call.message.chat.id, "Envoie le message à diffuser :\n\n/annuler pour annuler.")
        bot.register_next_step_handler(msg, lambda m: _traiter_broadcast(bot, m))

    elif data == "admin_add_premium":
        from telegram_bot.admin_handlers import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
        msg = bot.send_message(call.message.chat.id, "Format : `ID jours`\nExemple : `123456789 30`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m))

    elif data == "admin_remove_premium":
        from telegram_bot.admin_handlers import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
        msg = bot.send_message(call.message.chat.id, "Envoie l'ID utilisateur :")
        bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m))

    elif data in ["admin_gen_10", "admin_gen_30", "admin_gen_90"]:
        jours = int(data.split("_")[-1])
        codes = generer_lot_codes(jours, 10)
        log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
        texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
        for c in codes:
            texte += f"`{c}`\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

    elif data == "admin_gen_custom":
        from telegram_bot.admin_handlers import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
        msg = bot.send_message(call.message.chat.id, "Envoie : `jours quantite`\nExemple : `30 20`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m))

    elif data == "admin_voir_codes":
        codes = get_codes_disponibles(limite=30)
        texte = f"🎟️ **CODES DISPO**\n\n"
        for c in codes:
            texte += f"`{c['code']}` ({c['jours']}j)\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

    elif data.startswith("param_"):
        cle = data.replace("param_", "")
        from telegram_bot.admin_handlers import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: pass
        msg = bot.send_message(call.message.chat.id, f"Envoie la nouvelle valeur pour **{cle}** :\n\n/annuler pour annuler.", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m))

    elif data == "admin_voir_params":
        params = get_tous_parametres()
        texte = "⚙️ **PARAMETRES ACTUELS**\n\n"
        for p in params:
            texte += f"- **{p['cle']}** = `{p['valeur']}`\n"
        bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")


# --- Fonctions de traitement (importées pour être utilisées dans les lambdas) ---
# (Tu peux copier ces fonctions depuis admin_handlers.py, elles restent identiques)
def _traiter_broadcast(bot, message):
    from telegram_bot.admin_handlers import ADMIN_SESSIONS
    # ... (code identique) ...
    pass

def _traiter_gen_custom(bot, message):
    from telegram_bot.admin_handlers import ADMIN_SESSIONS
    # ... (code identique) ...
    pass

def _traiter_param(bot, message):
    from telegram_bot.admin_handlers import ADMIN_SESSIONS
    # ... (code identique) ...
    pass

def _traiter_add_premium(bot, message):
    from telegram_bot.admin_handlers import ADMIN_SESSIONS
    # ... (code identique) ...
    pass

def _traiter_remove_premium(bot, message):
    from telegram_bot.admin_handlers import ADMIN_SESSIONS
    # ... (code identique) ...
    pass
