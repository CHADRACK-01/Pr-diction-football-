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
    get_user_info
)
from users.db import get_connection


def _retirer_premium(user_id):
    """Retire le statut premium d'un utilisateur."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE utilisateurs
            SET status = 'free', date_expiration = NULL
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        rows = cur.rowcount
        cur.close()
        conn.close()
        return rows > 0
    except Exception as e:
        print(f"⚠️ Erreur _retirer_premium : {e}")
        return False


def enregistrer_admin_handlers(bot):

    # =========================================================
    # /admin
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("Stats", callback_data="admin|stats"),
            telebot.types.InlineKeyboardButton("Utilisateurs", callback_data="admin|users"),
            telebot.types.InlineKeyboardButton("Admins", callback_data="admin|admins"),
            telebot.types.InlineKeyboardButton("Parametres", callback_data="admin|params"),
            telebot.types.InlineKeyboardButton("Logs", callback_data="admin|logs"),
            telebot.types.InlineKeyboardButton("Bannis", callback_data="admin|bannis"),
        )

        bot.reply_to(
            message,
            "PANNEAU ADMIN\n\n"
            "Commandes disponibles :\n"
            "/stats : Statistiques\n"
            "/users : Liste utilisateurs\n"
            "/broadcast msg : Annonce\n"
            "/ban ID : Bannir\n"
            "/unban ID : Debannir\n"
            "/add_premium ID jours\n"
            "/remove_premium ID\n"
            "/add_admin ID\n"
            "/set_param cle valeur",
            reply_markup=markup
        )


    # =========================================================
    # CALLBACKS ADMIN
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin|"))
    def traiter_admin_callback(call):
        if not est_administrateur(call.from_user.id):
            bot.answer_callback_query(call.id, "Acces refuse.")
            return

        action = call.data.split("|")[1]
        bot.answer_callback_query(call.id, "OK")

        if action == "stats":
            stats = get_stats_globales()
            bot.send_message(
                call.message.chat.id,
                f"STATISTIQUES\n\n"
                f"Total : {stats.get('total', 0)}\n"
                f"Premium : {stats.get('premium', 0)}\n"
                f"Free : {stats.get('free', 0)}\n\n"
                f"Nouveaux (7j) : {stats.get('nouveaux_7j', 0)}\n"
                f"Nouveaux (24h) : {stats.get('nouveaux_24h', 0)}\n\n"
                f"Bannis : {stats.get('bannis', 0)}"
            )

        elif action == "users":
            users = get_liste_utilisateurs(limite=20)
            texte = "UTILISATEURS (20 derniers)\n\n"
            for i, u in enumerate(users, 1):
                statut = "P" if u['status'] == 'premium' else "F"
                texte += f"{i}. [{statut}] {u['first_name'] or 'Anonyme'} : {u['user_id']}\n"
            bot.send_message(call.message.chat.id, texte)

        elif action == "admins":
            admins = get_tous_admins()
            texte = "ADMINS\n\n"
            texte += "Principal : 8653408729\n\n"
            for a in admins:
                texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
            bot.send_message(call.message.chat.id, texte)

        elif action == "params":
            params = get_tous_parametres()
            if not params:
                bot.send_message(call.message.chat.id, "Aucun parametre defini.")
                return
            texte = "PARAMETRES\n\n"
            for p in params:
                texte += f"- {p['cle']} = {p['valeur']}\n"
            bot.send_message(call.message.chat.id, texte)

        elif action == "logs":
            logs = get_logs_admin(limite=15)
            if not logs:
                bot.send_message(call.message.chat.id, "Aucun log.")
                return
            texte = "LOGS ADMIN\n\n"
            for log in logs:
                texte += f"- {log['action']}\n  {log['admin_id']}\n  {log['details'][:40]}\n\n"
            bot.send_message(call.message.chat.id, texte)

        elif action == "bannis":
            bannis = get_liste_bannis()
            if not bannis:
                bot.send_message(call.message.chat.id, "Aucun banni.")
                return
            texte = "BANNIS\n\n"
            for b in bannis:
                texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
            bot.send_message(call.message.chat.id, texte)


    # =========================================================
    # /stats
    # =========================================================
    @bot.message_handler(commands=['stats'])
    def cmd_stats(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        stats = get_stats_globales()
        bot.reply_to(
            message,
            f"STATISTIQUES\n\n"
            f"Total : {stats.get('total', 0)}\n"
            f"Premium : {stats.get('premium', 0)}\n"
            f"Free : {stats.get('free', 0)}\n"
            f"Nouveaux 7j : {stats.get('nouveaux_7j', 0)}\n"
            f"Bannis : {stats.get('bannis', 0)}"
        )


    # =========================================================
    # /users
    # =========================================================
    @bot.message_handler(commands=['users'])
    def cmd_users(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        users = get_liste_utilisateurs(limite=30)
        texte = "30 DERNIERS UTILISATEURS\n\n"
        for i, u in enumerate(users, 1):
            statut = "P" if u['status'] == 'premium' else "F"
            texte += f"{i}. [{statut}] {u['first_name'] or '?'} : {u['user_id']}\n"
        bot.reply_to(message, texte)


    # =========================================================
    # /add_admin
    # =========================================================
    @bot.message_handler(commands=['add_admin'])
    def cmd_add_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Usage : /add_admin ID")
            return
        new_id = int(parts[1])
        if ajouter_admin(new_id):
            log_admin(message.from_user.id, "add_admin", f"ID: {new_id}")
            bot.reply_to(message, f"Admin {new_id} ajoute.")


    # =========================================================
    # /remove_admin
    # =========================================================
    @bot.message_handler(commands=['remove_admin'])
    def cmd_remove_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Usage : /remove_admin ID")
            return
        target = int(parts[1])
        if retirer_admin(target):
            log_admin(message.from_user.id, "remove_admin", f"ID: {target}")
            bot.reply_to(message, f"Admin {target} retire.")


    # =========================================================
    # /ban
    # =========================================================
    @bot.message_handler(commands=['ban'])
    def cmd_ban(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Usage : /ban ID raison")
            return
        target = int(parts[1])
        raison = parts[2] if len(parts) > 2 else ""
        if bannir_user(target, raison):
            log_admin(message.from_user.id, "ban", f"ID: {target}")
            bot.reply_to(message, f"Utilisateur {target} banni.")


    # =========================================================
    # /unban
    # =========================================================
    @bot.message_handler(commands=['unban'])
    def cmd_unban(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Usage : /unban ID")
            return
        target = int(parts[1])
        if debannir_user(target):
            log_admin(message.from_user.id, "unban", f"ID: {target}")
            bot.reply_to(message, f"Utilisateur {target} debanni.")


    # =========================================================
    # /add_premium
    # =========================================================
    @bot.message_handler(commands=['add_premium'])
    def cmd_add_premium(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Usage : /add_premium ID jours")
            return
        try:
            target = int(parts[1])
            jours = int(parts[2])
        except ValueError:
            bot.reply_to(message, "ID et jours doivent etre des nombres.")
            return
        expiration = (datetime.now() + timedelta(days=jours)).strftime("%Y-%m-%d %H:%M")
        if set_premium(target, expiration):
            log_admin(message.from_user.id, "add_premium", f"ID: {target} - {jours}j")
            bot.reply_to(
                message,
                f"Utilisateur {target} PREMIUM pour {jours} jours\n"
                f"Expire : {expiration}"
            )
            try:
                bot.send_message(
                    target,
                    f"Ton compte a ete passe en PREMIUM !\n\n"
                    f"Duree : {jours} jours\n"
                    f"Expire : {expiration}"
                )
            except Exception:
                pass


    # =========================================================
    # /remove_premium  ← NOUVEAU
    # =========================================================
    @bot.message_handler(commands=['remove_premium'])
    def cmd_remove_premium(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "Usage : /remove_premium ID")
            return
        target = int(parts[1])

        if _retirer_premium(target):
            log_admin(message.from_user.id, "remove_premium", f"ID: {target}")
            bot.reply_to(
                message,
                f"Utilisateur {target} est repasse en FREE."
            )
            try:
                bot.send_message(
                    target,
                    "Ton abonnement Premium a ete retire.\n\n"
                    "Tu peux continuer avec le statut FREE."
                )
            except Exception:
                pass
        else:
            bot.reply_to(message, "Utilisateur introuvable.")


    # =========================================================
    # /set_param
    # =========================================================
    @bot.message_handler(commands=['set_param'])
    def cmd_set_param(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "Usage : /set_param cle valeur")
            return
        cle = parts[1]
        valeur = parts[2]
        if set_parametre(cle, valeur):
            log_admin(message.from_user.id, "set_param", f"{cle} = {valeur}")
            bot.reply_to(message, f"{cle} = {valeur}")


    # =========================================================
    # /get_param
    # =========================================================
    @bot.message_handler(commands=['get_param'])
    def cmd_get_param(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage : /get_param cle")
            return
        val = get_parametre(parts[1], "Non defini")
        bot.reply_to(message, f"{parts[1]} = {val}")


    # =========================================================
    # /broadcast
    # =========================================================
    @bot.message_handler(commands=['broadcast'])
    def cmd_broadcast(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return
        texte = message.text.replace("/broadcast", "").strip()
        if not texte:
            bot.reply_to(message, "Usage : /broadcast ton message")
            return

        users = get_tous_utilisateurs()
        succes = 0
        echecs = 0
        for uid in users:
            try:
                bot.send_message(uid, f"ANNONCE ADMIN\n\n{texte}")
                succes += 1
                time.sleep(0.05)
            except Exception:
                echecs += 1

        log_admin(message.from_user.id, "broadcast", f"{succes} ok, {echecs} echecs")
        bot.reply_to(
            message,
            f"Broadcast termine\n\n"
            f"Envoyes : {succes}\n"
            f"Echecs : {echecs}"
        )
