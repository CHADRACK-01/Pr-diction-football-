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
        telebot.types.InlineKeyboardButton("❌ Fermer", callback_data="admin_close")
    )
    return markup

def _menu_premium():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("➕ Ajouter Premium", callback_data="admin_add_premium"),
        telebot.types.InlineKeyboardButton("➖ Retirer Premium", callback_data="admin_remove_premium"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup

def _menu_codes():
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

def _menu_parametres():
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

def _menu_bdd():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Taille BDD", callback_data="admin_taille_bdd"),
        telebot.types.InlineKeyboardButton("Detail tables", callback_data="admin_detail_tables"),
        telebot.types.InlineKeyboardButton("🧹 Nettoyer", callback_data="admin_nettoyer"),
        telebot.types.InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")
    )
    return markup


def enregistrer_admin_handlers(bot):

    # =========================================================
    # COMMANDE /admin (SECOURS)
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        bot.reply_to(message, "🎛️ **PANNEAU ADMIN**\n\nChoisis une action :", reply_markup=_menu_principal_admin(), parse_mode="Markdown")

    # =========================================================
    # ⚠️ NOUVEAU : CALLBACK DU BOUTON INLINE (Ouverture depuis le menu)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
    def open_admin_panel_callback(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return
        bot.answer_callback_query(call.id, "Ouverture du panneau...")
        bot.send_message(
            call.message.chat.id, 
            "🎛️ **PANNEAU ADMIN**\n\nChoisis une action :", 
            reply_markup=_menu_principal_admin(), 
            parse_mode="Markdown"
        )

    # =========================================================
    # CALLBACKS (Boutons Inline du panneau)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_") or call.data.startswith("param_") or call.data.startswith("bcast_"))
    def handle_admin_callbacks(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse")
            return
            
        data = call.data
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)

        # --- Navigation ---
        if data == "admin_back":
            bot.edit_message_text("🎛️ **PANNEAU ADMIN**\n\nChoisis une action :", call.message.chat.id, call.message.message_id, reply_markup=_menu_principal_admin(), parse_mode="Markdown")
        elif data == "admin_close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
        elif data == "admin_premium":
            bot.edit_message_text("💎 **GESTION PREMIUM**", call.message.chat.id, call.message.message_id, reply_markup=_menu_premium(), parse_mode="Markdown")
        elif data == "admin_codes":
            dispo = compter_codes_disponibles()
            bot.edit_message_text(f"🎟️ **CODES PREMIUM**\n\nCodes disponibles : {dispo}", call.message.chat.id, call.message.message_id, reply_markup=_menu_codes(), parse_mode="Markdown")
        elif data == "admin_bdd":
            bot.edit_message_text("🗄️ **BASE DE DONNÉES**", call.message.chat.id, call.message.message_id, reply_markup=_menu_bdd(), parse_mode="Markdown")
        elif data == "admin_params":
            bot.edit_message_text("⚙️ **PARAMÈTRES**", call.message.chat.id, call.message.message_id, reply_markup=_menu_parametres(), parse_mode="Markdown")

        # --- Stats ---
        elif data == "admin_stats":
            stats = get_stats_globales()
            texte = (
                f"📊 **STATISTIQUES**\n\n"
                f"Total : {stats.get('total', 0)}\nPremium : {stats.get('premium', 0)}\nFree : {stats.get('free', 0)}\n\n"
                f"Nouveaux (7j) : {stats.get('nouveaux_7j', 0)}\nNouveaux (24h) : {stats.get('nouveaux_24h', 0)}\n\nBannis : {stats.get('bannis', 0)}"
            )
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Utilisateurs ---
        elif data == "admin_users":
            users = get_liste_utilisateurs(limite=20)
            texte = "👥 **UTILISATEURS (20 derniers)**\n\n"
            for i, u in enumerate(users, 1):
                statut = "💎" if u['status'] == 'premium' else "🆓"
                texte += f"{i}. {statut} {u['first_name'] or '?'} : `{u['user_id']}`\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Paiements ---
        elif data == "admin_payments":
            demandes = get_demandes_en_attente(limite=10)
            if not demandes:
                bot.send_message(call.message.chat.id, "Aucun paiement en attente.")
                return
            bot.send_message(call.message.chat.id, f"{len(demandes)} paiement(s) en attente :")
            for d in demandes:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                    telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}")
                )
                try:
                    bot.send_photo(call.message.chat.id, d['preuve_photo_id'], caption=f"#{d['id']} - User `{d['user_id']}`\nAbo: {d['abonnement']}\nMontant: {d['montant']} CDF", reply_markup=markup, parse_mode="Markdown")
                except Exception: pass

        # --- BDD ---
        elif data == "admin_taille_bdd":
            bot.send_message(call.message.chat.id, f"🗄️ Taille totale : **{get_taille_base()}**", parse_mode="Markdown")
        elif data == "admin_detail_tables":
            tables = get_detail_tables()
            texte = "🗄️ **DETAIL PAR TABLE**\n\n"
            for t in tables[:10]:
                texte += f"• {t['table_name']} : {t['size']} ({t['rows']} lignes)\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
        elif data == "admin_nettoyer":
            logs = nettoyer_logs_anciens(jours=30)
            paiements = nettoyer_paiements_anciens(jours=90)
            bot.send_message(call.message.chat.id, f"🧹 Nettoyage terminé\n\n• {logs} log(s) supprimé(s)\n• {paiements} paiement(s) supprimé(s)")

        # --- Admins ---
        elif data == "admin_admins":
            admins = get_tous_admins()
            texte = "👑 **ADMINS**\n\nPrincipal : `8653408729`\n\n"
            for a in admins:
                texte += f"- `{a['user_id']}` : {a['nom'] or 'Sans nom'}\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Logs ---
        elif data == "admin_logs":
            logs = get_logs_admin(limite=15)
            if not logs:
                bot.send_message(call.message.chat.id, "Aucun log.")
                return
            texte = "📝 **LOGS ADMIN**\n\n"
            for log in logs:
                texte += f"- {log['action']}\n  Par : `{log['admin_id']}`\n  {log['details'][:40]}\n\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Bannis ---
        elif data == "admin_bannis":
            bannis = get_liste_bannis()
            if not bannis:
                bot.send_message(call.message.chat.id, "Aucun banni.")
                return
            texte = "🚫 **BANNIS**\n\n"
            for b in bannis:
                texte += f"- `{b['user_id']}` : {b['raison'] or 'Sans raison'}\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Broadcast ---
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
            bot.register_next_step_handler(msg, _traiter_broadcast)

        # --- Premium ---
        elif data == "admin_add_premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            msg = bot.send_message(call.message.chat.id, "Format : `ID jours`\nExemple : `123456789 30`", parse_mode="Markdown")
            bot.register_next_step_handler(msg, _traiter_add_premium)
        elif data == "admin_remove_premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            msg = bot.send_message(call.message.chat.id, "Envoie l'ID utilisateur :")
            bot.register_next_step_handler(msg, _traiter_remove_premium)

        # --- Codes ---
        elif data in ["admin_gen_10", "admin_gen_30", "admin_gen_90"]:
            jours = int(data.split("_")[-1])
            codes = generer_lot_codes(jours, 10)
            log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
            texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
            for c in codes:
                texte += f"`{c}`\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")
        elif data == "admin_gen_custom":
            ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
            msg = bot.send_message(call.message.chat.id, "Envoie : `jours quantite`\nExemple : `30 20`", parse_mode="Markdown")
            bot.register_next_step_handler(msg, _traiter_gen_custom)
        elif data == "admin_voir_codes":
            codes = get_codes_disponibles(limite=30)
            if not codes:
                bot.send_message(call.message.chat.id, "Aucun code disponible.")
                return
            texte = f"🎟️ **CODES DISPONIBLES ({len(codes)})**\n\n"
            for c in codes:
                texte += f"`{c['code']}` ({c['jours']}j)\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        # --- Paramètres ---
        elif data.startswith("param_"):
            cle = data.replace("param_", "")
            ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
            msg = bot.send_message(call.message.chat.id, f"Envoie la nouvelle valeur pour **{cle}** :\n\n/annuler pour annuler.", parse_mode="Markdown")
            bot.register_next_step_handler(msg, _traiter_param)
        elif data == "admin_voir_params":
            params = get_tous_parametres()
            if not params:
                bot.send_message(call.message.chat.id, "Aucun paramètre défini.")
                return
            texte = "⚙️ **PARAMETRES ACTUELS**\n\n"
            for p in params:
                texte += f"- **{p['cle']}** = `{p['valeur']}`\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")


    # =========================================================
    # TRAITEMENTS (Next Step Handlers)
    # =========================================================
    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        if not est_administrateur(message.from_user.id): return
        ADMIN_SESSIONS.pop(message.from_user.id, None)
        bot.reply_to(message, "Action annulee.")

    def _traiter_gen_custom(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
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
            texte += f"`{c}`\n"
        bot.reply_to(message, texte, parse_mode="Markdown")

        ADMIN_SESSIONS.pop(user_id, None)

    def _traiter_param(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.")
            return

        session = ADMIN_SESSIONS.get(user_id, {})
        cle = session.get("cle")

        if not cle:
            bot.reply_to(message, "Erreur session.")
            return

        if set_parametre(cle, texte):
            log_admin(user_id, "set_param", f"{cle} = {texte}")
            bot.reply_to(message, f"✅ **{cle}** a été mis à jour sur : `{texte}`", parse_mode="Markdown")

        ADMIN_SESSIONS.pop(user_id, None)

    def _traiter_broadcast(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.")
            return

        if not texte:
            bot.reply_to(message, "Message vide.")
            return

        session = ADMIN_SESSIONS.get(user_id, {})
        cible = session.get("cible", "users")

        users = get_tous_utilisateurs() if cible in ["users", "all"] else []
        admins = get_tous_admins()
        envoyer_canal = cible in ["canal", "all"]

        bot.reply_to(message, "🚀 Diffusion lancée en arrière-plan. Tu recevras un récapitulatif à la fin.")
        
        lancer_broadcast_async(bot, users, texte, admins, canal=envoyer_canal)
        
        log_admin(user_id, "broadcast", f"Cible: {cible}")
        ADMIN_SESSIONS.pop(user_id, None)

    def _traiter_add_premium(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
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
            bot.reply_to(message, f"✅ Utilisateur `{target}` PREMIUM pour {jours} jours\nExpire : {expiration}", parse_mode="Markdown")
            try:
                bot.send_message(target, f"💎 Ton compte a été passé en PREMIUM !\n\nDurée : {jours} jours\nExpire : {expiration}")
            except Exception: pass
        else:
            bot.reply_to(message, "Utilisateur introuvable.")

        ADMIN_SESSIONS.pop(user_id, None)

    def _traiter_remove_premium(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.")
            return

        if not texte.isdigit():
            bot.reply_to(message, "ID invalide.")
            return

        target = int(texte)

        if _retirer_premium(target):
            log_admin(user_id, "remove_premium", f"ID: {target}")
            bot.reply_to(message, f"✅ Utilisateur `{target}` est repassé en FREE.", parse_mode="Markdown")
            try:
                bot.send_message(target, "Ton abonnement Premium a été retiré.")
            except Exception: pass
        else:
            bot.reply_to(message, "Utilisateur introuvable.")

        ADMIN_SESSIONS.pop(user_id, None)
