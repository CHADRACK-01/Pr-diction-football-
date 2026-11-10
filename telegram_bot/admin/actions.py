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
from core.utils.logs import log_info, log_error, log_warning
from telegram_bot.admin.menus import (
    menu_premium, menu_codes, menu_bdd, menu_parametres
)

ADMIN_SESSIONS = {}


def _retirer_premium(user_id):
    """Retire le premium d'un utilisateur (avec log d'erreur)."""
    try:
        conn = get_connection()
        conn.execute("UPDATE utilisateurs SET status = 'free', date_expiration = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        log_info(f"Premium retiré pour {user_id}", "ADMIN")
        return True
    except Exception as e:
        log_error(f"Impossible de retirer le premium de {user_id}", "ADMIN", exception=e)
        return False


# =========================================================
# GESTIONNAIRE POUR LES BOUTONS INLINE
# =========================================================
def executer_action(bot, call, data, user_id):
    log_info(f"EXECUTION ACTION INLINE : '{data}' demandée par {user_id}", "ADMIN")

    try:
        # =========================================================
        # STATS
        # =========================================================
        if data == "admin_stats":
            try:
                stats = get_stats_globales()
            except Exception as e:
                log_error("Impossible de récupérer les stats globales", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les statistiques.")
                return
            texte = f"📊 STATISTIQUES\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}"
            bot.send_message(call.message.chat.id, texte)
        
        # =========================================================
        # UTILISATEURS
        # =========================================================
        elif data == "admin_users":
            try:
                users = get_liste_utilisateurs(limite=20)
            except Exception as e:
                log_error("Impossible de récupérer la liste des utilisateurs", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les utilisateurs.")
                return
            texte = "👥 UTILISATEURS\n\n"
            for u in users:
                statut = "💎" if u['status'] == 'premium' else "🆓"
                texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
            bot.send_message(call.message.chat.id, texte)

        # =========================================================
        # PAIEMENTS EN ATTENTE
        # =========================================================
        elif data == "admin_payments":
            try:
                demandes = get_demandes_en_attente(limite=10)
            except Exception as e:
                log_error("Impossible de récupérer les paiements en attente", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les paiements.")
                return
            if not demandes:
                bot.send_message(call.message.chat.id, "Aucun paiement en attente.")
                return
            for d in demandes:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                    telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}")
                )
                try:
                    bot.send_photo(call.message.chat.id, d['preuve_photo_id'], caption=f"#{d['id']} - User {d['user_id']}\nMontant: {d['montant']} CDF", reply_markup=markup)
                except Exception as e:
                    log_warning(f"Impossible d'envoyer la photo de paiement #{d['id']} : {e}", "ADMIN")

        # =========================================================
        # BASE DE DONNÉES
        # =========================================================
        elif data == "admin_taille_bdd":
            try:
                taille = get_taille_base()
            except Exception as e:
                log_error("Impossible de récupérer la taille de la BDD", "ADMIN", exception=e)
                taille = "Erreur"
            bot.send_message(call.message.chat.id, f"🗄️ Taille totale : {taille}")
        
        elif data == "admin_detail_tables":
            try:
                tables = get_detail_tables()
            except Exception as e:
                log_error("Impossible de récupérer les détails des tables", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les détails.")
                return
            if not tables:
                bot.send_message(call.message.chat.id, "❌ Aucun détail disponible.")
                return
            texte = "🗄️ DETAIL PAR TABLE\n\n"
            for t in tables[:10]:
                texte += f"• {t['table_name']} : {t['size']}\n"
            bot.send_message(call.message.chat.id, texte)

        elif data == "admin_nettoyer":
            try:
                logs = nettoyer_logs_anciens(jours=30)
                paiements = nettoyer_paiements_anciens(jours=90)
                bot.send_message(call.message.chat.id, f"🧹 Nettoyage terminé\n• {logs} log(s)\n• {paiements} paiement(s)")
            except Exception as e:
                log_error("Erreur lors du nettoyage", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Erreur lors du nettoyage.")

        # =========================================================
        # ADMINS / LOGS / BANNIS
        # =========================================================
        elif data == "admin_admins":
            try:
                admins = get_tous_admins()
            except Exception as e:
                log_error("Impossible de récupérer la liste des admins", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les admins.")
                return
            texte = "👑 ADMINS\n\nPrincipal : 8653408729\n\n"
            for a in admins:
                texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
            bot.send_message(call.message.chat.id, texte)

        elif data == "admin_logs":
            try:
                logs = get_logs_admin(limite=15)
            except Exception as e:
                log_error("Impossible de récupérer les logs admin", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les logs.")
                return
            texte = "📝 LOGS ADMIN\n\n"
            for log in logs:
                texte += f"- {log['action']} (Par {log['admin_id']})\n"
            bot.send_message(call.message.chat.id, texte)

        elif data == "admin_bannis":
            try:
                bannis = get_liste_bannis()
            except Exception as e:
                log_error("Impossible de récupérer la liste des bannis", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les bannis.")
                return
            texte = "🚫 BANNIS\n\n"
            for b in bannis:
                texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
            bot.send_message(call.message.chat.id, texte)

        # =========================================================
        # PARAMÈTRES
        # =========================================================
        elif data == "admin_params_menu":
            bot.edit_message_text("⚙️ PARAMÈTRES\n\nChoisis un paramètre :", call.message.chat.id, call.message.message_id, reply_markup=menu_parametres())

        elif data.startswith("param_"):
            cle = data.replace("param_", "")
            ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
            bot.delete_message(call.message.chat.id, call.message.message_id)
            try:
                msg = bot.send_message(call.message.chat.id, f"Envoie la nouvelle valeur pour {cle} :\n\n/annuler pour annuler.")
                bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error(f"Impossible d'enregistrer le handler pour le paramètre {cle}", "ADMIN", exception=e)

        elif data == "admin_voir_params":
            try:
                params = get_tous_parametres()
            except Exception as e:
                log_error("Impossible de récupérer les paramètres", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les paramètres.")
                return
            texte = "⚙️ PARAMETRES ACTUELS\n\n"
            for p in params:
                texte += f"- {p['cle']} = {p['valeur']}\n"
            bot.send_message(call.message.chat.id, texte)

        # =========================================================
        # PREMIUM
        # =========================================================
        elif data == "admin_premium":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("💎 GESTION PREMIUM", call.message.chat.id, call.message.message_id, reply_markup=menu_premium())
        
        elif data == "admin_add_premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            try:
                msg = bot.send_message(call.message.chat.id, "Format : ID jours\nExemple : 123456789 30")
                bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler add_premium", "ADMIN", exception=e)

        elif data == "admin_remove_premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            try:
                msg = bot.send_message(call.message.chat.id, "Envoie l'ID utilisateur :")
                bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler remove_premium", "ADMIN", exception=e)

        # =========================================================
        # CODES PREMIUM
        # =========================================================
        elif data == "admin_codes":
            ADMIN_SESSIONS.pop(user_id, None)
            try:
                dispo = compter_codes_disponibles()
            except Exception as e:
                log_error("Impossible de compter les codes disponibles", "ADMIN", exception=e)
                dispo = "?"
            bot.edit_message_text(f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=menu_codes())

        elif data in ["admin_gen_10", "admin_gen_30", "admin_gen_90"]:
            jours = int(data.split("_")[-1])
            try:
                codes = generer_lot_codes(jours, 10)
                log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
                texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
                for c in codes:
                    texte += f"{c}\n"
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(f"Impossible de générer 10 codes de {jours}j", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Erreur lors de la génération des codes.")

        elif data == "admin_gen_custom":
            ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
            try:
                msg = bot.send_message(call.message.chat.id, "Envoie : jours quantite\nExemple : 30 20")
                bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler gen_custom", "ADMIN", exception=e)

        elif data == "admin_voir_codes":
            try:
                codes = get_codes_disponibles(limite=30)
            except Exception as e:
                log_error("Impossible de récupérer les codes disponibles", "ADMIN", exception=e)
                bot.send_message(call.message.chat.id, "❌ Impossible de récupérer les codes.")
                return
            if not codes:
                bot.send_message(call.message.chat.id, "Aucun code disponible.")
                return
            texte = f"🎟️ CODES DISPO\n\n"
            for c in codes:
                texte += f"{c['code']} ({c['jours']}j)\n"
            bot.send_message(call.message.chat.id, texte)

        # =========================================================
        # BROADCAST
        # =========================================================
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
            try:
                msg = bot.send_message(call.message.chat.id, "Envoie le message à diffuser :\n\n/annuler pour annuler.")
                bot.register_next_step_handler(msg, lambda m: _traiter_broadcast(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler broadcast", "ADMIN", exception=e)

        # =========================================================
        # BDD
        # =========================================================
        elif data == "admin_bdd":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text("🗄️ BASE DE DONNÉES", call.message.chat.id, call.message.message_id, reply_markup=menu_bdd())

        else:
            log_warning(f"Action inline inconnue : '{data}'", "ADMIN")
            bot.send_message(call.message.chat.id, f"⚠️ Action '{data}' non reconnue.")
    
    except Exception as e:
        log_error(f"Erreur exécution action inline '{data}'", "ADMIN", exception=e)


# =========================================================
# GESTIONNAIRE POUR LES BOUTONS EN BAS
# =========================================================
def executer_action_bas(bot, message, text, user_id):
    log_info(f"EXECUTION ACTION BAS : '{text}' demandée par {user_id}", "ADMIN")

    try:
        # =========================================================
        # STATS / UTILISATEURS / PAIEMENTS
        # =========================================================
        if text == "📊 Stats":
            try:
                stats = get_stats_globales()
            except Exception as e:
                log_error("Impossible de récupérer les stats", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les stats.")
                return
            texte = f"📊 STATISTIQUES\n\nTotal : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}"
            bot.send_message(message.chat.id, texte)
        
        elif text == "👥 Utilisateurs":
            try:
                users = get_liste_utilisateurs(limite=20)
            except Exception as e:
                log_error("Impossible de récupérer les utilisateurs", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les utilisateurs.")
                return
            texte = "👥 UTILISATEURS\n\n"
            for u in users:
                statut = "💎" if u['status'] == 'premium' else "🆓"
                texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
            bot.send_message(message.chat.id, texte)

        elif text == "💳 Paiements":
            try:
                demandes = get_demandes_en_attente(limite=10)
            except Exception as e:
                log_error("Impossible de récupérer les paiements", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les paiements.")
                return
            if not demandes:
                bot.send_message(message.chat.id, "Aucun paiement en attente.")
                return
            for d in demandes:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                    telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}")
                )
                try:
                    bot.send_photo(message.chat.id, d['preuve_photo_id'], caption=f"#{d['id']} - User {d['user_id']}\nMontant: {d['montant']} CDF", reply_markup=markup)
                except Exception as e:
                    log_warning(f"Impossible d'envoyer la photo {d['id']} : {e}", "ADMIN")

        # =========================================================
        # BASE DE DONNÉES
        # =========================================================
        elif text == "Taille BDD":
            try:
                taille = get_taille_base()
            except Exception as e:
                log_error("Impossible de récupérer la taille BDD", "ADMIN", exception=e)
                taille = "Erreur"
            bot.send_message(message.chat.id, f"🗄️ Taille totale : {taille}")
        
        elif text == "Detail tables":
            try:
                tables = get_detail_tables()
            except Exception as e:
                log_error("Impossible de récupérer les détails des tables", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les détails.")
                return
            if not tables:
                bot.send_message(message.chat.id, "❌ Aucun détail disponible.")
                return
            texte = "🗄️ DETAIL PAR TABLE\n\n"
            for t in tables[:10]:
                texte += f"• {t['table_name']} : {t['size']}\n"
            bot.send_message(message.chat.id, texte)
            
        elif text == "🧹 Nettoyer":
            try:
                logs = nettoyer_logs_anciens(jours=30)
                paiements = nettoyer_paiements_anciens(jours=90)
                bot.send_message(message.chat.id, f"🧹 Nettoyage terminé\n• {logs} log(s)\n• {paiements} paiement(s)")
            except Exception as e:
                log_error("Erreur lors du nettoyage", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Erreur lors du nettoyage.")

        # =========================================================
        # ADMINS / LOGS / BANNIS
        # =========================================================
        elif text == "👑 Admins":
            try:
                admins = get_tous_admins()
            except Exception as e:
                log_error("Impossible de récupérer les admins", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les admins.")
                return
            texte = "👑 ADMINS\n\nPrincipal : 8653408729\n\n"
            for a in admins:
                texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
            bot.send_message(message.chat.id, texte)

        elif text == "📝 Logs":
            try:
                logs = get_logs_admin(limite=15)
            except Exception as e:
                log_error("Impossible de récupérer les logs", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les logs.")
                return
            texte = "📝 LOGS ADMIN\n\n"
            for log in logs:
                texte += f"- {log['action']} (Par {log['admin_id']})\n"
            bot.send_message(message.chat.id, texte)

        elif text == "🚫 Bannis":
            try:
                bannis = get_liste_bannis()
            except Exception as e:
                log_error("Impossible de récupérer les bannis", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les bannis.")
                return
            texte = "🚫 BANNIS\n\n"
            for b in bannis:
                texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
            bot.send_message(message.chat.id, texte)

        # =========================================================
        # PARAMÈTRES
        # =========================================================
        elif text.startswith("Heure notifs") or text.startswith("Limite Free") or text.startswith("Prix Stars") or text.startswith("Message accueil") or text.startswith("Mode maintenance"):
            cle = text.lower().replace(" ", "_")
            ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
            try:
                msg = bot.send_message(message.chat.id, f"Envoie la nouvelle valeur pour {text} :\n\n/annuler pour annuler.")
                bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler param", "ADMIN", exception=e)

        elif text == "👁️ Voir parametres":
            try:
                params = get_tous_parametres()
            except Exception as e:
                log_error("Impossible de récupérer les paramètres", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les paramètres.")
                return
            texte = "⚙️ PARAMETRES ACTUELS\n\n"
            for p in params:
                texte += f"- {p['cle']} = {p['valeur']}\n"
            bot.send_message(message.chat.id, texte)

        # =========================================================
        # PREMIUM
        # =========================================================
        elif text == "➕ Ajouter Premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            try:
                msg = bot.send_message(message.chat.id, "Format : ID jours\nExemple : 123456789 30")
                bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler add_premium", "ADMIN", exception=e)

        elif text == "➖ Retirer Premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            try:
                msg = bot.send_message(message.chat.id, "Envoie l'ID utilisateur :")
                bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler remove_premium", "ADMIN", exception=e)

        # =========================================================
        # CODES PREMIUM
        # =========================================================
        elif text in ["Gen 10 jours", "Gen 30 jours", "Gen 90 jours"]:
            jours = int(text.split()[1])
            try:
                codes = generer_lot_codes(jours, 10)
                log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
                texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
                for c in codes:
                    texte += f"{c}\n"
                bot.send_message(message.chat.id, texte)
            except Exception as e:
                log_error(f"Impossible de générer 10 codes de {jours}j", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Erreur lors de la génération des codes.")

        elif text == "Gen custom":
            ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
            try:
                msg = bot.send_message(message.chat.id, "Envoie : jours quantite\nExemple : 30 20")
                bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error("Impossible d'enregistrer le handler gen_custom", "ADMIN", exception=e)

        elif text == "👁️ Voir codes dispo":
            try:
                codes = get_codes_disponibles(limite=30)
            except Exception as e:
                log_error("Impossible de récupérer les codes dispo", "ADMIN", exception=e)
                bot.send_message(message.chat.id, "❌ Impossible de récupérer les codes.")
                return
            if not codes:
                bot.send_message(message.chat.id, "Aucun code disponible.")
                return
            texte = f"🎟️ CODES DISPO\n\n"
            for c in codes:
                texte += f"{c['code']} ({c['jours']}j)\n"
            bot.send_message(message.chat.id, texte)

        # =========================================================
        # BROADCAST
        # =========================================================
        elif text == "📢 Broadcast":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("📱 Utilisateurs + 📢 Canal", callback_data="bcast_all"),
                telebot.types.InlineKeyboardButton("📱 Utilisateurs uniquement", callback_data="bcast_users"),
                telebot.types.InlineKeyboardButton("📢 Canal uniquement", callback_data="bcast_canal")
            )
            bot.send_message(message.chat.id, "Où veux-tu envoyer l'annonce ?", reply_markup=markup)

        else:
            log_warning(f"Action bas inconnue : '{text}'", "ADMIN")
            bot.send_message(message.chat.id, f"⚠️ Action '{text}' non reconnue.")
    
    except Exception as e:
        log_error(f"Erreur exécution action bas '{text}'", "ADMIN", exception=e)


# =========================================================
# FONCTIONS DE TRAITEMENT (next_step_handler)
# =========================================================
def _traiter_param(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    session = sessions.get(user_id, {})
    cle = session.get("cle")

    if not cle:
        log_warning(f"Session param invalide pour {user_id}", "ADMIN")
        bot.reply_to(message, "❌ Erreur de session. Réessaie.")
        sessions.pop(user_id, None)
        return

    try:
        if set_parametre(cle, texte):
            log_admin(user_id, "set_param", f"{cle} = {texte}")
            bot.reply_to(message, f"✅ {cle} a été mis à jour sur : {texte}")
        else:
            bot.reply_to(message, "❌ Impossible de mettre à jour le paramètre.")
    except Exception as e:
        log_error(f"Impossible de mettre à jour le paramètre '{cle}'", "ADMIN", exception=e)
        bot.reply_to(message, "❌ Erreur lors de la mise à jour.")
    finally:
        sessions.pop(user_id, None)


def _traiter_gen_custom(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "❌ Format invalide. Usage : jours quantite")
        sessions.pop(user_id, None)
        return

    jours = int(parts[0])
    quantite = int(parts[1])

    if quantite > 100:
        bot.reply_to(message, "❌ Maximum 100 codes.")
        sessions.pop(user_id, None)
        return

    try:
        codes = generer_lot_codes(jours, quantite)
        log_admin(user_id, "gen_codes_custom", f"{quantite} codes de {jours}j")

        texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
        for c in codes:
            texte += f"{c}\n"
        bot.reply_to(message, texte)
    except Exception as e:
        log_error(f"Impossible de générer {quantite} codes de {jours}j", "ADMIN", exception=e)
        bot.reply_to(message, "❌ Erreur lors de la génération.")
    finally:
        sessions.pop(user_id, None)


def _traiter_add_premium(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "❌ Format invalide. Usage : ID jours")
        sessions.pop(user_id, None)
        return

    target = int(parts[0])
    jours = int(parts[1])
    expiration = (datetime.now() + timedelta(days=jours)).strftime("%Y-%m-%d %H:%M")

    try:
        if set_premium(target, expiration):
            log_admin(user_id, "add_premium", f"ID: {target} - {jours}j")
            bot.reply_to(message, f"✅ Utilisateur {target} PREMIUM pour {jours} jours\nExpire : {expiration}")
            try:
                bot.send_message(target, f"💎 Ton compte a été passé en PREMIUM !\n\nDurée : {jours} jours\nExpire : {expiration}")
            except Exception as e:
                log_warning(f"Impossible de notifier {target} de son premium : {e}", "ADMIN")
        else:
            bot.reply_to(message, "❌ Utilisateur introuvable.")
    except Exception as e:
        log_error(f"Impossible d'ajouter premium à {target}", "ADMIN", exception=e)
        bot.reply_to(message, "❌ Erreur lors de l'ajout du premium.")
    finally:
        sessions.pop(user_id, None)


def _traiter_remove_premium(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    if not texte.isdigit():
        bot.reply_to(message, "❌ ID invalide.")
        sessions.pop(user_id, None)
        return

    target = int(texte)

    try:
        if _retirer_premium(target):
            log_admin(user_id, "remove_premium", f"ID: {target}")
            bot.reply_to(message, f"✅ Utilisateur {target} est repassé en FREE.")
            try:
                bot.send_message(target, "Ton abonnement Premium a été retiré.")
            except Exception as e:
                log_warning(f"Impossible de notifier {target} du retrait premium : {e}", "ADMIN")
        else:
            bot.reply_to(message, "❌ Impossible de retirer le premium.")
    except Exception as e:
        log_error(f"Erreur retrait premium {target}", "ADMIN", exception=e)
        bot.reply_to(message, "❌ Erreur lors du retrait.")
    finally:
        sessions.pop(user_id, None)


def _traiter_broadcast(bot, message, sessions):
    user_id = message.from_user.id
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    if not texte:
        bot.reply_to(message, "❌ Message vide.")
        sessions.pop(user_id, None)
        return

    session = sessions.get(user_id, {})
    cible = session.get("cible", "users")

    try:
        users = get_tous_utilisateurs() if cible in ["users", "all"] else []
        admins = get_tous_admins()
        envoyer_canal = cible in ["canal", "all"]

        bot.reply_to(message, "🚀 Diffusion lancée en arrière-plan. Tu recevras un récapitulatif à la fin.")
        lancer_broadcast_async(bot, users, texte, admins, canal=envoyer_canal)
        log_admin(user_id, "broadcast", f"Cible: {cible}")
    except Exception as e:
        log_error(f"Impossible de lancer le broadcast (cible={cible})", "ADMIN", exception=e)
        bot.reply_to(message, "❌ Erreur lors du lancement du broadcast.")
    finally:
        sessions.pop(user_id, None)
