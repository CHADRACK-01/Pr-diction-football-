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


# Sessions temporaires pour les conversations admin
ADMIN_SESSIONS = {}


def _retirer_premium(user_id):
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


def _menu_admin():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Stats"),
        telebot.types.KeyboardButton("Utilisateurs"),
        telebot.types.KeyboardButton("Admins"),
        telebot.types.KeyboardButton("Parametres"),
        telebot.types.KeyboardButton("Logs"),
        telebot.types.KeyboardButton("Bannis"),
        telebot.types.KeyboardButton("Broadcast"),
        telebot.types.KeyboardButton("Premium"),
        telebot.types.KeyboardButton("Retour Menu"),
    )
    return markup


def _menu_premium():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Ajouter Premium"),
        telebot.types.KeyboardButton("Retirer Premium"),
        telebot.types.KeyboardButton("Retour Admin"),
    )
    return markup


def enregistrer_admin_handlers(bot):

    # =========================================================
    # /admin (commande texte)
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return

        bot.reply_to(
            message,
            "PANNEAU ADMIN\n\n"
            "Choisis une action dans le menu ci-dessous :",
            reply_markup=_menu_admin()
        )


    # =========================================================
    # GESTION DES BOUTONS ADMIN
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user and est_administrateur(m.from_user.id) and m.text in [
        "Panneau Admin", "Stats", "Utilisateurs", "Admins", "Parametres",
        "Logs", "Bannis", "Broadcast", "Premium", "Retour Menu",
        "Ajouter Premium", "Retirer Premium", "Retour Admin"
    ])
    def handle_admin_buttons(message):
        text = message.text
        user_id = message.from_user.id

        # --- Ouvrir le panneau admin ---
        if text == "Panneau Admin":
            bot.reply_to(
                message,
                "PANNEAU ADMIN\n\n"
                "Choisis une action :",
                reply_markup=_menu_admin()
            )
            return

        # --- Retour menu principal ---
        if text == "Retour Menu":
            from telegram_bot.handlers import _envoyer_menu_principal
            _envoyer_menu_principal(message.chat.id, user_id, bot)
            return

        # --- Retour au menu admin ---
        if text == "Retour Admin":
            bot.reply_to(
                message,
                "PANNEAU ADMIN",
                reply_markup=_menu_admin()
            )
            return

        # =========================================================
        # STATS
        # =========================================================
        if text == "Stats":
            stats = get_stats_globales()
            bot.reply_to(
                message,
                f"STATISTIQUES\n\n"
                f"Total : {stats.get('total', 0)}\n"
                f"Premium : {stats.get('premium', 0)}\n"
                f"Free : {stats.get('free', 0)}\n\n"
                f"Nouveaux (7j) : {stats.get('nouveaux_7j', 0)}\n"
                f"Nouveaux (24h) : {stats.get('nouveaux_24h', 0)}\n\n"
                f"Bannis : {stats.get('bannis', 0)}"
            )

        # =========================================================
        # UTILISATEURS
        # =========================================================
        elif text == "Utilisateurs":
            users = get_liste_utilisateurs(limite=20)
            texte = "UTILISATEURS (20 derniers)\n\n"
            for i, u in enumerate(users, 1):
                statut = "P" if u['status'] == 'premium' else "F"
                texte += f"{i}. [{statut}] {u['first_name'] or '?'} : {u['user_id']}\n"
            bot.reply_to(message, texte)

        # =========================================================
        # ADMINS
        # =========================================================
        elif text == "Admins":
            admins = get_tous_admins()
            texte = "ADMINS\n\n"
            texte += "Principal : 8653408729\n\n"
            for a in admins:
                texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
            bot.reply_to(message, texte)

        # =========================================================
        # PARAMETRES
        # =========================================================
        elif text == "Parametres":
            params = get_tous_parametres()
            if not params:
                bot.reply_to(message, "Aucun parametre defini.")
                return
            texte = "PARAMETRES\n\n"
            for p in params:
                texte += f"- {p['cle']} = {p['valeur']}\n"
            bot.reply_to(message, texte)

        # =========================================================
        # LOGS
        # =========================================================
        elif text == "Logs":
            logs = get_logs_admin(limite=15)
            if not logs:
                bot.reply_to(message, "Aucun log.")
                return
            texte = "LOGS ADMIN\n\n"
            for log in logs:
                texte += f"- {log['action']}\n  {log['admin_id']}\n  {log['details'][:40]}\n\n"
            bot.reply_to(message, texte)

        # =========================================================
        # BANNIS
        # =========================================================
        elif text == "Bannis":
            bannis = get_liste_bannis()
            if not bannis:
                bot.reply_to(message, "Aucun banni.")
                return
            texte = "BANNIS\n\n"
            for b in bannis:
                texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
            bot.reply_to(message, texte)

        # =========================================================
        # BROADCAST
        # =========================================================
        elif text == "Broadcast":
            ADMIN_SESSIONS[user_id] = {"action": "broadcast"}
            msg = bot.reply_to(
                message,
                "Envoie le message a diffuser a tous les utilisateurs.\n\n"
                "Tape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_broadcast)

        # =========================================================
        # PREMIUM (sous-menu)
        # =========================================================
        elif text == "Premium":
            bot.reply_to(
                message,
                "GESTION PREMIUM\n\n"
                "Choisis une action :",
                reply_markup=_menu_premium()
            )

        # =========================================================
        # AJOUTER PREMIUM
        # =========================================================
        elif text == "Ajouter Premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            msg = bot.reply_to(
                message,
                "Envoie l'ID utilisateur et le nombre de jours :\n\n"
                "Format : ID jours\n"
                "Exemple : 123456789 30\n\n"
                "Tape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_add_premium)

        # =========================================================
        # RETIRER PREMIUM
        # =========================================================
        elif text == "Retirer Premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            msg = bot.reply_to(
                message,
                "Envoie l'ID utilisateur a repasser en FREE.\n\n"
                "Tape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_remove_premium)


    # =========================================================
    # TRAITEMENTS DES CONVERSATIONS
    # =========================================================
    def _traiter_broadcast(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.", reply_markup=_menu_admin())
            return

        if not texte:
            bot.reply_to(message, "Message vide.")
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

        log_admin(user_id, "broadcast", f"{succes} ok, {echecs} echecs")
        bot.reply_to(
            message,
            f"Broadcast termine\n\n"
            f"Envoyes : {succes}\n"
            f"Echecs : {echecs}",
            reply_markup=_menu_admin()
        )
        ADMIN_SESSIONS.pop(user_id, None)


    def _traiter_add_premium(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.", reply_markup=_menu_admin())
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
            bot.reply_to(
                message,
                f"Utilisateur {target} PREMIUM pour {jours} jours\n"
                f"Expire : {expiration}",
                reply_markup=_menu_admin()
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
        else:
            bot.reply_to(message, "Utilisateur introuvable.", reply_markup=_menu_admin())

        ADMIN_SESSIONS.pop(user_id, None)


    def _traiter_remove_premium(message):
        user_id = message.from_user.id
        texte = message.text

        if texte == "/annuler":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.reply_to(message, "Annule.", reply_markup=_menu_admin())
            return

        if not texte.isdigit():
            bot.reply_to(message, "ID invalide.")
            return

        target = int(texte)

        if _retirer_premium(target):
            log_admin(user_id, "remove_premium", f"ID: {target}")
            bot.reply_to(
                message,
                f"Utilisateur {target} est repasse en FREE.",
                reply_markup=_menu_admin()
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
            bot.reply_to(message, "Utilisateur introuvable.", reply_markup=_menu_admin())

        ADMIN_SESSIONS.pop(user_id, None)


    # =========================================================
    # COMMANDES ADMIN (toujours disponibles)
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
            f"Free : {stats.get('free', 0)}"
        )


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


    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        user_id = message.from_user.id
        ADMIN_SESSIONS.pop(user_id, None)
        bot.reply_to(message, "Action annulee.")


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
