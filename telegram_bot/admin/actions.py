# telegram_bot/admin/actions.py
"""
Actions admin (inline + bas).
"""

import telebot
from datetime import datetime, timedelta

from users import (
    get_stats_globales, get_liste_utilisateurs, get_tous_admins,
    log_admin, get_logs_admin, get_parametre, set_parametre,
    get_tous_parametres, set_premium, get_tous_utilisateurs,
    get_demandes_en_attente, get_codes_disponibles, generer_lot_codes,
    compter_codes_disponibles, get_taille_base, get_detail_tables,
    nettoyer_logs_anciens, nettoyer_paiements_anciens,
    ajouter_jours_premium, get_liste_bannis, utilisateur_existe,
    get_user_info,
)
from core.broadcast_manager import lancer_broadcast_async
from core.utils.logs import log_info, log_error, log_warning
from telegram_bot.admin.menus import (
    menu_premium, menu_codes, menu_bdd, menu_parametres,
)

ADMIN_SESSIONS = {}


def _contexte(message_or_user):
    user = getattr(message_or_user, "from_user", message_or_user)
    return {
        "user_id": user.id,
        "user_name": user.first_name or "",
        "username": user.username or "",
    }


def _retirer_premium(user_id, ctx=None):
    from users.db import db_execute
    rowcount = db_execute(
        "UPDATE utilisateurs SET status = 'free', date_expiration = NULL WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "utilisateurs", "operation": "remove_premium"},
    )
    if rowcount is None or rowcount == 0:
        log_error(
            message="Impossible de retirer le premium",
            module="ADMIN",
            user_context=ctx,
            extra={"target_user_id": user_id},
        )
        return False
    log_info(f"Premium retiré pour {user_id}", "ADMIN", user_context=ctx)
    return True


def executer_action(bot, call, data, user_id):
    ctx = {
        "user_id": user_id,
        "user_name": call.from_user.first_name or "",
        "username": call.from_user.username or "",
        "chat_id": call.message.chat.id,
    }
    log_info(f"Action inline : {data}", "ADMIN", user_context=ctx)

    try:
        if data == "admin_stats":
            try:
                stats = get_stats_globales()
                texte = (
                    f"📊 STATISTIQUES\n\n"
                    f"Total : {stats.get('total', 0)}\n"
                    f"Premium : {stats.get('premium', 0)}\n"
                    f"Free : {stats.get('free', 0)}"
                )
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(message="Erreur stats", module="ADMIN", user_context=ctx, exception=e)
                bot.send_message(call.message.chat.id, "❌ Erreur stats.")

        elif data == "admin_users":
            try:
                users = get_liste_utilisateurs(limite=20)
                texte = "👥 UTILISATEURS\n\n"
                for u in users:
                    statut = "💎" if u["status"] == "premium" else "🆓"
                    texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(message="Erreur utilisateurs", module="ADMIN", user_context=ctx, exception=e)
                bot.send_message(call.message.chat.id, "❌ Erreur utilisateurs.")

        elif data == "admin_payments":
            try:
                demandes = get_demandes_en_attente(limite=10)
                if not demandes:
                    bot.send_message(call.message.chat.id, "Aucun paiement en attente.")
                    return
                for d in demandes:
                    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                        telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}"),
                    )
                    try:
                        bot.send_photo(
                            call.message.chat.id, d["preuve_photo_id"],
                            caption=f"#{d['id']} - User {d['user_id']}\nMontant: {d['montant']} CDF",
                            reply_markup=markup,
                        )
                    except Exception as e:
                        log_warning(message="Impossible d'envoyer la photo", module="ADMIN", exception=e)
            except Exception as e:
                log_error(message="Erreur paiements", module="ADMIN", user_context=ctx, exception=e)

        elif data == "admin_bdd":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text(
                "🗄️ BASE DE DONNÉES", call.message.chat.id,
                call.message.message_id, reply_markup=menu_bdd(),
            )

        elif data.startswith("param_"):
            cle = data.replace("param_", "", 1)
            ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            try:
                msg = bot.send_message(
                    call.message.chat.id,
                    f"Envoie la nouvelle valeur pour {cle} :\n\n/annuler pour annuler.",
                )
                bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m, ADMIN_SESSIONS))
            except Exception as e:
                log_error(message="Impossible d'enregistrer handler param", module="ADMIN", user_context=ctx, exception=e)

        elif data == "admin_voir_params":
            try:
                params = get_tous_parametres()
                texte = "⚙️ PARAMETRES\n\n"
                for p in params:
                    texte += f"- {p['cle']} = {p['valeur']}\n"
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(message="Erreur params", module="ADMIN", user_context=ctx, exception=e)

        elif data == "admin_premium":
            ADMIN_SESSIONS.pop(user_id, None)
            bot.edit_message_text(
                "💎 GESTION PREMIUM", call.message.chat.id,
                call.message.message_id, reply_markup=menu_premium(),
            )

        elif data == "admin_add_premium":
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            msg = bot.send_message(
                call.message.chat.id,
                "Format : ID jours\nExemple : 123456789 30",
            )
            bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m, ADMIN_SESSIONS))

        elif data == "admin_remove_premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            msg = bot.send_message(call.message.chat.id, "Envoie l'ID utilisateur :")
            bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m, ADMIN_SESSIONS))

        elif data == "admin_codes":
            ADMIN_SESSIONS.pop(user_id, None)
            try:
                dispo = compter_codes_disponibles()
            except Exception:
                dispo = "?"
            bot.edit_message_text(
                f"🎟️ CODES PREMIUM\n\nCodes disponibles : {dispo}",
                call.message.chat.id, call.message.message_id,
                reply_markup=menu_codes(),
            )

        elif data in ("admin_gen_10", "admin_gen_30", "admin_gen_90"):
            jours = int(data.split("_")[-1])
            try:
                codes = generer_lot_codes(jours, 10)
                log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
                texte = f"🎟️ {len(codes)} code(s) généré(s) pour {jours} jours :\n\n"
                for c in codes:
                    texte += f"{c}\n"
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(message="Erreur génération codes", module="ADMIN", user_context=ctx, exception=e)

        elif data == "admin_gen_custom":
            ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
            msg = bot.send_message(call.message.chat.id, "Envoie : jours quantite\nExemple : 30 20")
            bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m, ADMIN_SESSIONS))

        elif data == "admin_voir_codes":
            try:
                codes = get_codes_disponibles(limite=30)
                if not codes:
                    bot.send_message(call.message.chat.id, "Aucun code disponible.")
                    return
                texte = "🎟️ CODES DISPO\n\n"
                for c in codes:
                    texte += f"{c['code']} ({c['jours']}j)\n"
                bot.send_message(call.message.chat.id, texte)
            except Exception as e:
                log_error(message="Erreur voir codes", module="ADMIN", user_context=ctx, exception=e)

        elif data == "admin_broadcast":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("📱 Utilisateurs + 📢 Canal", callback_data="bcast_all"),
                telebot.types.InlineKeyboardButton("📱 Utilisateurs uniquement", callback_data="bcast_users"),
                telebot.types.InlineKeyboardButton("📢 Canal uniquement", callback_data="bcast_canal"),
            )
            bot.send_message(call.message.chat.id, "Où envoyer l'annonce ?", reply_markup=markup)

        elif data.startswith("bcast_"):
            cible = data.split("_", 1)[1]
            ADMIN_SESSIONS[user_id] = {"action": "broadcast", "cible": cible}
            msg = bot.send_message(
                call.message.chat.id,
                "Envoie le message à diffuser :\n\n/annuler pour annuler.",
            )
            bot.register_next_step_handler(msg, lambda m: _traiter_broadcast(bot, m, ADMIN_SESSIONS))

        elif data == "admin_features":
            from core.feature_flags import lister_features
            features = lister_features()
            texte = "⚙️ **GESTION DES FONCTIONNALITÉS**\n\n"
            if not features:
                texte += "Aucune fonctionnalité enregistrée."
            else:
                for fid, actif in features.items():
                    statut = "✅ ACTIF" if actif else "❌ INACTIF"
                    texte += f"• {fid} : {statut}\n"
            texte += "\nCommandes :\n`/activer <id>`\n`/desactiver <id>`"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        else:
            log_warning(message=f"Action inline inconnue : {data}", module="ADMIN", user_context=ctx)
            bot.send_message(call.message.chat.id, f"⚠️ Action '{data}' non reconnue.")

    except Exception as e:
        log_error(message=f"Erreur action inline '{data}'", module="ADMIN", user_context=ctx, exception=e)


def executer_action_bas(bot, message, text, user_id):
    ctx = _contexte(message)
    log_info(f"Action bas : {text}", "ADMIN", user_context=ctx)

    try:
        if text == "📊 Stats":
            stats = get_stats_globales()
            bot.send_message(
                message.chat.id,
                f"📊 STATISTIQUES\n\n"
                f"Total : {stats.get('total', 0)}\n"
                f"Premium : {stats.get('premium', 0)}\n"
                f"Free : {stats.get('free', 0)}",
            )

        elif text == "👥 Utilisateurs":
            users = get_liste_utilisateurs(limite=20)
            texte = "👥 UTILISATEURS\n\n"
            for u in users:
                statut = "💎" if u["status"] == "premium" else "🆓"
                texte += f"{statut} {u['first_name'] or '?'} : {u['user_id']}\n"
            bot.send_message(message.chat.id, texte)

        elif text == "💳 Paiements":
            demandes = get_demandes_en_attente(limite=10)
            if not demandes:
                bot.send_message(message.chat.id, "Aucun paiement en attente.")
                return
            for d in demandes:
                markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    telebot.types.InlineKeyboardButton("✅ Valider", callback_data=f"vpay|{d['id']}"),
                    telebot.types.InlineKeyboardButton("❌ Refuser", callback_data=f"rpay|{d['id']}"),
                )
                try:
                    bot.send_photo(
                        message.chat.id, d["preuve_photo_id"],
                        caption=f"#{d['id']} - User {d['user_id']}\nMontant: {d['montant']} CDF",
                        reply_markup=markup,
                    )
                except Exception as e:
                    log_warning(message="Erreur envoi photo", module="ADMIN", exception=e)

        elif text == "Taille BDD":
            bot.send_message(message.chat.id, f"🗄️ Taille : {get_taille_base()}")

        elif text == "Detail tables":
            tables = get_detail_tables()
            texte = "🗄️ DETAIL PAR TABLE\n\n"
            for t in tables:
                texte += f"• {t['table_name']} : {t['size']}\n"
            bot.send_message(message.chat.id, texte)

        elif text == "🧹 Nettoyer":
            logs = nettoyer_logs_anciens(jours=30)
            paiements = nettoyer_paiements_anciens(jours=90)
            bot.send_message(message.chat.id, f"🧹 {logs} log(s), {paiements} paiement(s)")

        elif text == "👑 Admins":
            admins = get_tous_admins()
            texte = "👑 ADMINS\n\n"
            for a in admins:
                texte += f"- {a['user_id']} : {a['nom'] or 'Sans nom'}\n"
            bot.send_message(message.chat.id, texte)

        elif text == "📝 Logs":
            logs = get_logs_admin(limite=15)
            texte = "📝 LOGS\n\n"
            for lg in logs:
                texte += f"- {lg['action']} (par {lg['admin_id']})\n"
            bot.send_message(message.chat.id, texte)

        elif text == "🚫 Bannis":
            bannis = get_liste_bannis()
            texte = "🚫 BANNIS\n\n"
            for b in bannis:
                texte += f"- {b['user_id']} : {b['raison'] or 'Sans raison'}\n"
            bot.send_message(message.chat.id, texte)

        elif text in ("➕ Ajouter Premium",):
            ADMIN_SESSIONS[user_id] = {"action": "add_premium"}
            msg = bot.send_message(message.chat.id, "Format : ID jours")
            bot.register_next_step_handler(msg, lambda m: _traiter_add_premium(bot, m, ADMIN_SESSIONS))

        elif text == "➖ Retirer Premium":
            ADMIN_SESSIONS[user_id] = {"action": "remove_premium"}
            msg = bot.send_message(message.chat.id, "Envoie l'ID utilisateur :")
            bot.register_next_step_handler(msg, lambda m: _traiter_remove_premium(bot, m, ADMIN_SESSIONS))

        elif text in ("Gen 10 jours", "Gen 30 jours", "Gen 90 jours"):
            jours = int(text.split()[1])
            codes = generer_lot_codes(jours, 10)
            log_admin(user_id, "gen_codes", f"10 codes de {jours}j")
            texte = f"🎟️ {len(codes)} codes ({jours}j) :\n\n" + "\n".join(codes)
            bot.send_message(message.chat.id, texte)

        elif text == "Gen custom":
            ADMIN_SESSIONS[user_id] = {"action": "gen_custom"}
            msg = bot.send_message(message.chat.id, "Format : jours quantite")
            bot.register_next_step_handler(msg, lambda m: _traiter_gen_custom(bot, m, ADMIN_SESSIONS))

        elif text == "👁️ Voir codes dispo":
            codes = get_codes_disponibles(limite=30)
            if not codes:
                bot.send_message(message.chat.id, "Aucun code.")
                return
            texte = "🎟️ CODES\n\n" + "\n".join(f"{c['code']} ({c['jours']}j)" for c in codes)
            bot.send_message(message.chat.id, texte)

        elif text == "📢 Broadcast":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("📱 Utilisateurs + 📢 Canal", callback_data="bcast_all"),
                telebot.types.InlineKeyboardButton("📱 Utilisateurs", callback_data="bcast_users"),
                telebot.types.InlineKeyboardButton("📢 Canal", callback_data="bcast_canal"),
            )
            bot.send_message(message.chat.id, "Cible ?", reply_markup=markup)

        elif text.startswith(("Heure notifs", "Limite Free", "Prix Stars",
                              "Message accueil", "Mode maintenance")):
            cle = text.lower().replace(" ", "_")
            ADMIN_SESSIONS[user_id] = {"action": "param", "cle": cle}
            msg = bot.send_message(message.chat.id, f"Nouvelle valeur pour {text} :")
            bot.register_next_step_handler(msg, lambda m: _traiter_param(bot, m, ADMIN_SESSIONS))

        elif text == "👁️ Voir parametres":
            params = get_tous_parametres()
            texte = "⚙️ PARAMS\n\n" + "\n".join(f"- {p['cle']} = {p['valeur']}" for p in params)
            bot.send_message(message.chat.id, texte)

        elif text == "⚙️ Gérer les Fonctionnalités":
            from core.feature_flags import lister_features
            features = lister_features()
            texte = "⚙️ FONCTIONNALITÉS\n\n"
            if not features:
                texte += "Aucune fonctionnalité enregistrée."
            else:
                for fid, actif in features.items():
                    statut = "✅" if actif else "❌"
                    texte += f"{statut} {fid}\n"
            texte += "\nCommandes :\n/activer <id>\n/desactiver <id>"
            bot.send_message(message.chat.id, texte)

        else:
            log_warning(message=f"Action bas inconnue : {text}", module="ADMIN", user_context=ctx)
            bot.send_message(message.chat.id, f"⚠️ Action '{text}' non reconnue.")

    except Exception as e:
        log_error(message=f"Erreur action bas '{text}'", module="ADMIN", user_context=ctx, exception=e)


# =========================================================
# TRAITEMENTS next_step
# =========================================================
def _traiter_param(bot, message, sessions):
    user_id = message.from_user.id
    ctx = _contexte(message)
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    session = sessions.get(user_id, {})
    cle = session.get("cle")
    if not cle:
        log_warning(message="Session param invalide", module="ADMIN", user_context=ctx)
        sessions.pop(user_id, None)
        bot.reply_to(message, "❌ Erreur de session.")
        return

    try:
        if set_parametre(cle, texte):
            log_admin(user_id, "set_param", f"{cle} = {texte}")
            bot.reply_to(message, f"✅ {cle} = {texte}")
        else:
            bot.reply_to(message, "❌ Impossible de mettre à jour.")
    except Exception as e:
        log_error(message=f"Erreur maj paramètre '{cle}'", module="ADMIN", user_context=ctx, exception=e)
        bot.reply_to(message, "❌ Erreur.")
    finally:
        sessions.pop(user_id, None)


def _traiter_gen_custom(bot, message, sessions):
    user_id = message.from_user.id
    ctx = _contexte(message)
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "❌ Format : jours quantite")
        sessions.pop(user_id, None)
        return

    jours, quantite = int(parts[0]), int(parts[1])
    if quantite > 100:
        bot.reply_to(message, "❌ Max 100 codes.")
        sessions.pop(user_id, None)
        return

    try:
        codes = generer_lot_codes(jours, quantite)
        log_admin(user_id, "gen_codes_custom", f"{quantite} codes de {jours}j")
        texte_out = f"🎟️ {len(codes)} codes ({jours}j) :\n\n" + "\n".join(codes)
        bot.reply_to(message, texte_out)
    except Exception as e:
        log_error(message="Erreur génération codes custom", module="ADMIN", user_context=ctx, exception=e)
        bot.reply_to(message, "❌ Erreur.")
    finally:
        sessions.pop(user_id, None)


def _traiter_add_premium(bot, message, sessions):
    user_id = message.from_user.id
    ctx = _contexte(message)
    texte = message.text or ""

    if texte == "/annuler":
        sessions.pop(user_id, None)
        bot.reply_to(message, "Annulé.")
        return

    parts = texte.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.reply_to(message, "❌ Format : ID jours")
        sessions.pop(user_id, None)
        return

    target = int(parts[0])
    jours = int(parts[1])

    if not utilisateur_existe(target):
        log_warning(
            message="Tentative d'ajout premium sur utilisateur inexistant",
            module="ADMIN",
            user_context=ctx,
            extra={"target_user_id": target},
        )
        bot.reply_to(message, f"❌ Utilisateur {target} introuvable.")
        sessions.pop(user_id, None)
        return

    if not ajouter_jours_premium(target, jours):
        log_error(
            message="Impossible d'ajouter du premium",
            module="ADMIN",
            user_context=ctx,
            extra={"target_user_id": target, "jours": jours},
        )
        bot.reply_to(message, "❌ Impossible d'ajouter le premium.")
        sessions.pop(user_id, None)
        return

    log_admin(user_id, "add_premium", f"ID: {target} - {jours}j")
    info = get_user_info(target)
    expiration = info.get("date_expiration", "?") if info else "?"
    bot.reply_to(message, f"✅ {target} PREMIUM +{jours}j (expire {expiration})")

    try:
        bot.send_message(target, f"💎 Ton compte a été passé en PREMIUM !\n+{jours} jours\nExpire : {expiration}")
    except Exception as e:
        log_warning(
            message="Impossible de notifier l'utilisateur premium",
            module="ADMIN",
            user_context=ctx,
            extra={"target_user_id": target},
            exception=e,
        )
    sessions.pop(user_id, None)


def _traiter_remove_premium(bot, message, sessions):
    user_id = message.from_user.id
    ctx = _contexte(message)
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
    if not _retirer_premium(target, ctx):
        bot.reply_to(message, f"❌ Impossible de retirer le premium de {target}.")
        sessions.pop(user_id, None)
        return

    log_admin(user_id, "remove_premium", f"ID: {target}")
    bot.reply_to(message, f"✅ {target} est repassé en FREE.")
    try:
        bot.send_message(target, "Ton abonnement Premium a été retiré.")
    except Exception as e:
        log_warning(
            message="Impossible de notifier retrait premium",
            module="ADMIN",
            user_context=ctx,
            exception=e,
        )
    sessions.pop(user_id, None)


def _traiter_broadcast(bot, message, sessions):
    user_id = message.from_user.id
    ctx = _contexte(message)
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
        users = get_tous_utilisateurs() if cible in ("users", "all") else []
        admins = get_tous_admins()
        envoyer_canal = cible in ("canal", "all")

        bot.reply_to(message, "🚀 Diffusion lancée en arrière-plan.")
        lancer_broadcast_async(bot, users, texte, admins, canal=envoyer_canal)
        log_admin(user_id, "broadcast", f"Cible: {cible}")
    except Exception as e:
        log_error(message="Erreur lancement broadcast", module="ADMIN", user_context=ctx, exception=e)
        bot.reply_to(message, "❌ Erreur.")
    finally:
        sessions.pop(user_id, None)


# =========================================================
# COMMANDES FEATURES (hors session)
# =========================================================
# Note : Ces commandes sont aussi ajoutées dans admin_handlers.py pour être actives
def cmd_features(bot, message):
    from users import est_administrateur
    if not est_administrateur(message.from_user.id): return
    from core.feature_flags import lister_features
    features = lister_features()
    texte = "⚙️ **GESTION DES FONCTIONNALITÉS**\n\n"
    if not features:
        texte += "Aucune fonctionnalité enregistrée."
    else:
        for fid, actif in features.items():
            statut = "✅ ACTIF" if actif else "❌ INACTIF"
            texte += f"• {fid} : {statut}\n"
    texte += "\nPour activer : `/activer 413`\nPour désactiver : `/desactiver 413`"
    bot.send_message(message.chat.id, texte, parse_mode="Markdown")

def cmd_activer(bot, message):
    from users import est_administrateur
    if not est_administrateur(message.from_user.id): return
    try:
        fid = message.text.split()[1]
        from core.feature_flags import activer_feature
        activer_feature(fid)
        bot.reply_to(message, f"✅ Fonctionnalité {fid} ACTIVÉE.")
    except Exception:
        bot.reply_to(message, "Format: /activer <id>")

def cmd_desactiver(bot, message):
    from users import est_administrateur
    if not est_administrateur(message.from_user.id): return
    try:
        fid = message.text.split()[1]
        from core.feature_flags import desactiver_feature
        desactiver_feature(fid)
        bot.reply_to(message, f"❌ Fonctionnalité {fid} DÉSACTIVÉE.")
    except Exception:
        bot.reply_to(message, "Format: /desactiver <id>")

def cmd_taux(bot, message):
    """Commande /taux pour voir et modifier les taux de change."""
    from users import est_administrateur
    if not est_administrateur(message.from_user.id): 
        return
    
    from core.devises import get_taux_change
    from users.admin import set_parametre
    
    args = message.text.split()
    if len(args) < 3:
        # Afficher les taux actuels
        taux_usd = get_taux_change("USD")
        taux_eur = get_taux_change("EUR")
        bot.reply_to(message, 
            f"💱 <b>TAUX DE CHANGE ACTUELS</b>\n\n"
            f"1 USD = {taux_usd} CDF\n"
            f"1 EUR = {taux_eur} CDF\n\n"
            f"Pour modifier : <code>/taux USD 2850</code>",
            parse_mode="HTML"
        )
        return
    
    devise = args[1].upper()
    try:
        nouveau_taux = float(args[2])
        if set_parametre(f"taux_{devise.lower()}", str(nouveau_taux)):
            bot.reply_to(message, f"✅ Taux {devise} mis à jour : 1 {devise} = {nouveau_taux} CDF")
        else:
            bot.reply_to(message, "❌ Erreur lors de la mise à jour.")
    except ValueError:
        bot.reply_to(message, "❌ Format invalide. Exemple : /taux USD 2850")
