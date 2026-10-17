import telebot
from datetime import datetime, timedelta

from users import (
    get_stats_globales, get_liste_utilisateurs, get_tous_admins,
    log_admin, get_logs_admin, get_parametre, set_parametre,
    get_tous_parametres, set_premium, get_tous_utilisateurs,
    get_demandes_en_attente, get_codes_disponibles, generer_lot_codes,
    compter_codes_disponibles, get_taille_base, get_detail_tables,
    nettoyer_logs_anciens, nettoyer_paiements_anciens
)
from users.db import get_connection
from core.broadcast_manager import lancer_broadcast_async
from core.utils.logs import log_info, log_error

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

    if data == "admin_stats":
        stats = get_stats_globales()
        texte = f"📊 STATISTIQUES\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}"
        bot.send_message(call.message.chat.id, texte)
    
    elif data == "admin_users":
        users = get_liste_utilisateurs(limite=20)
        texte = "👥 UTILISATEURS\n\n"
        for u in users:
            statut = "💎" if u['status'] == 'premium' else "🆓"
            texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
        bot.send_message(call.message.chat.id, texte)

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

    elif data == "admin_taille_bdd":
        bot.send_message(call.message.chat.id, f"🗄️ Taille totale : {get_taille_base()}")
    
    elif data == "admin_detail_tables":
        log_info("Tentative de récupération des détails des tables...", "ADMIN")
        try:
            tables = get_detail_tables()
            log_info(f"Résultat get_detail_tables : {len(tables)} tables trouvées.", "ADMIN")
            if not tables:
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les détails (base vide ou droits insuffisants).")
                return
            texte = "🗄️ DETAIL PAR TABLE\n\n"
            for t in tables[:10]:
                texte += f"• {t['table_name']} : {t['size']}\n"
            bot.send_message(call.message.chat.id, texte)
        except Exception as e:
            log_error(f"Erreur admin_detail_tables : {e}", "ADMIN", e)
            bot.send_message(call.message.chat.id, f"❌ Erreur : {e}")

    elif data == "admin_nettoyer":
        logs = nettoyer_logs_anciens(jours=30)
        paiements = nettoyer_paiements_anciens(jours=90)
        bot.send_message(call.message.chat.id, f"🧹 Nettoyage terminé\n• {logs} log(s)\n• {paiements} paiement(s)")

    elif data == "admin_admins":
        admins = get_tous_admins()
        texte = "👑 ADMINS\n\nPrincipal : 8653408729\n\n"
        for a in admins:
            texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
        bot.send_message(call.message.chat.id, texte)

    elif data == "admin_logs":
        logs = get_logs_admin(limite=15)
        texte = "📝 LOGS ADMIN\n\n"
        for log in logs:
            texte += f"- {log['action']} (Par {log['admin_id']})\n"
        bot.send_message(call.message.chat.id, texte)

    elif data == "admin_bannis":
        from users import get_liste_bannis
        bannis = get_liste_bannis()
        texte = "🚫 BANNIS\n\n"
        for b in bannis:
            texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
        bot.send_message(call.message.chat.id, texte)

    # --- PARAMÈTRES ---
    elif data == "admin_params_menu":  # On utilisera un nouveau nom pour éviter les conflits
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

    # --- AUTRES ACTIONS (déléguées) ---
    elif data == "admin_premium":
        ADMIN_SESSIONS.pop(user_id, None)
        bot.edit_message_text("💎 GESTION PREMIUM", call.message.chat.id, call.message.message_id, reply_markup=menu_premium())
    
    elif data == "admin_codes":
        ADMIN_SESSIONS.pop(user_id, None)
        dispo = compter_codes_disponibles()
        bot.edit_message_text(f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=menu_codes())

    elif data == "admin_bdd":
        ADMIN_SESSIONS.pop(user_id, None)
        bot.edit_message_text("🗄️ BASE DE DONNÉES", call.message.chat.id, call.message.message_id, reply_markup=menu_bdd())

    else:
        log_info(f"Aucune action trouvée pour '{data}'", "ADMIN")
        bot.send_message(call.message.chat.id, f"⚠️ Action '{data}' non reconnue.")
