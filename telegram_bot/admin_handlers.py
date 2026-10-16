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
        telebot.types.KeyboardButton("Paiements"),
        telebot.types.KeyboardButton("Codes"),
        telebot.types.KeyboardButton("Base de donnees"),
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
    # /admin
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "Acces refuse.")
            return

        bot.reply_to(
            message,
            "PANNEAU ADMIN\n\nChoisis une action dans le menu ci-dessous :",
            reply_markup=_menu_admin()
        )


    # =========================================================
    # /gen_codes
    # =========================================================
    @bot.message_handler(commands=['gen_codes'])
    def cmd_gen_codes(message):
        if not est_administrateur(message.from_user.id):
            return

        parts = message.text.split()
        if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
            bot.reply_to(message, "Usage : /gen_codes jours quantite")
            return

        jours = int(parts[1])
        quantite = int(parts[2])

        if quantite > 100:
            bot.reply_to(message, "Maximum 100 codes par lot.")
            return

        codes = generer_lot_codes(jours, quantite)

        if not codes:
            bot.reply_to(message, "Erreur generation.")
            return

        log_admin(message.from_user.id, "gen_codes", f"{quantite} codes de {jours}j")

        texte = f"{len(codes)} code(s) genere(s) pour {jours} jours :\n\n"
        for c in codes:
            texte += f"`{c}`\n"

        bot.reply_to(message, texte, parse_mode="Markdown")


    # =========================================================
    # /nettoyer
    # =========================================================
    @bot.message_handler(commands=['nettoyer'])
    def cmd_nettoyer(message):
        if not est_administrateur(message.from_user.id):
            return

        logs = nettoyer_logs_anciens(jours=30)
        paiements = nettoyer_paiements_anciens(jours=90)

        bot.reply_to(
            message,
            f"🧹 Nettoyage termine\n\n"
            f"• {logs} log(s) supprime(s)\n"
            f"• {paiements} paiement(s) supprime(s)"
        )


    # =========================================================
    # COMMANDES ADMIN (texte)
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


    @bot.message_handler(commands=['annuler'])
    def cmd_annuler(message):
        user_id = message.from_user.id
        ADMIN_SESSIONS.pop(user_id, None)
        bot.reply_to(message, "Action annulee.")


    # =========================================================
    # GESTION DES BOUTONS ADMIN
    # =========================================================
    @bot.message_handler(func=lambda m: m.from_user and est_administrateur(m.from_user.id) and m.text in [
        "Panneau Admin", "Stats", "Utilisateurs", "Admins", "Parametres",
        "Logs", "Bannis", "Broadcast", "Premium", "Retour Menu",
        "Ajouter Premium", "Retirer Premium", "Retour Admin",
        "Paiements", "Codes", "Base de donnees"
    ])
    def handle_admin_buttons(message):
        text = message.text
        user_id = message.from_user.id

        # --- Ouvrir le panneau admin ---
        if text == "Panneau Admin":
            bot.reply_to(
                message,
                "PANNEAU ADMIN\n\nChoisis une action :",
                reply_markup=_menu_admin()
            )
            return

        # --- Retour menu principal ---
        if text == "Retour Menu":
            from telegram_bot.menu_handlers import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
            return

        # --- Retour au menu admin ---
        if text == "Retour Admin":
            bot.reply_to(message, "PANNEAU ADMIN", reply_markup=_menu_admin())
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
        # PAIEMENTS EN ATTENTE
        # =========================================================
        elif text == "Paiements":
            demandes = get_demandes_en_attente(limite=10)

            if not demandes:
                bot.reply_to(message, "Aucun paiement en attente.")
                return

            bot.reply_to(message, f"{len(demandes)} paiement(s) en attente :")

            for d in demandes:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                    telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}")
                )

                try:
                    bot.send_photo(
                        message.chat.id,
                        d['preuve_photo_id'],
                        caption=f"#{d['id']} - User {d['user_id']}\nAbo: {d['abonnement']}\nMontant: {d['montant']} CDF",
                        reply_markup=markup
                    )
                except Exception as e:
                    print(f"Erreur envoi photo : {e}")

        # =========================================================
        # CODES PREMIUM
        # =========================================================
        elif text == "Codes":
            dispo = compter_codes_disponibles()
            texte = (
                f"CODES PREMIUM\n\n"
                f"Codes disponibles : {dispo}\n\n"
                f"Commandes :\n"
                f"/gen_codes jours quantite\n"
                f"Exemple : /gen_codes 30 10"
            )
            bot.reply_to(message, texte)

        # =========================================================
        # BASE DE DONNEES
        # =========================================================
        elif text == "Base de donnees":
            taille = get_taille_base()
            tables = get_detail_tables()

            texte = f"BASE DE DONNEES\n\nTaille totale : {taille}\n\n"
            texte += "Detail par table :\n"
            for t in tables[:10]:
                texte += f"• {t['table_name']} : {t['size']} ({t['rows']} lignes)\n"

            texte += "\nCommande : /nettoyer"

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
                "Envoie le message a diffuser a tous les utilisateurs.\n\nTape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_broadcast)

        # =========================================================
        # PREMIUM
        # =========================================================
        elif text == "Premium":
            bot.reply_to(
                message,
                "GESTION PREMIUM\n\nChoisis une action :",
                reply_markup=_menu_premium()
            )

        elif text == "Ajouter Premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            msg = bot.reply_to(
                message,
                "Envoie l'ID utilisateur et le nombre de jours :\n\n"
                "Format : ID jours\nExemple : 123456789 30\n\nTape /annuler pour annuler."
            )
            bot.register_next_step_handler(msg, _traiter_add_premium)

        elif text == "Retirer Premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            msg = bot.reply_to(
                message,
                "Envoie l'ID utilisateur a repasser en FREE.\n\nTape /annuler pour annuler."
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
            f"Broadcast termine\n\nEnvoyes : {succes}\nEchecs : {echecs}",
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
                f"Utilisateur {target} PREMIUM pour {jours} jours\nExpire : {expiration}",
                reply_markup=_menu_admin()
            )
            try:
                bot.send_message(
                    target,
                    f"Ton compte a ete passe en PREMIUM !\n\nDuree : {jours} jours\nExpire : {expiration}"
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
                    "Ton abonnement Premium a ete retire.\n\nTu peux continuer avec le statut FREE."
                )
            except Exception:
                pass
        else:
            bot.reply_to(message, "Utilisateur introuvable.", reply_markup=_menu_admin())

        ADMIN_SESSIONS.pop(user_id, None)
