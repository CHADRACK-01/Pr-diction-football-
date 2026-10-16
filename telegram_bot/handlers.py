import threading
import io
import time
import joblib
import telebot
from datetime import datetime, timedelta

from config import FICHIER_HISTORIQUE
from users import (
    enregistrer_utilisateur, get_statut_label, peut_faire_pronostic,
    get_compteur_jour, get_limite_jour, incrementer_compteur, est_premium,
    charger_modele_cache,
    activer_notifications, desactiver_notifications,
    est_administrateur, get_stats_globales, get_liste_utilisateurs,
    ajouter_admin, retirer_admin, get_tous_admins,
    bannir_user, debannir_user, est_banni, get_liste_bannis,
    log_admin, get_logs_admin,
    get_parametre, set_parametre, get_tous_parametres,
    get_user_info, set_premium, get_tous_utilisateurs
)
from core.ml_model import global_model_data, tache_arriere_plan_maj
from core.prediction import predire_match, sauvegarder_historique


_chargement_en_cours = False


def _charger_modele_si_necessaire(message, bot):
    global _chargement_en_cours

    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True

    if _chargement_en_cours:
        bot.reply_to(message, "⏳ Chargement déjà en cours, patiente...")
        return False

    _chargement_en_cours = True

    try:
        cache = charger_modele_cache()
        if not cache:
            bot.reply_to(message, "⚠️ Aucun modèle en cache. Contacte l'administrateur.")
            _chargement_en_cours = False
            return False

        modele_bytes, precision, nb_matchs = cache
        print(f"⚡ Chargement du cache ({nb_matchs} matchs, précision={round(precision*100, 2)}%)...")

        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)

        global_model_data['df'] = donnees['df']
        global_model_data['teams'] = donnees['teams']
        global_model_data['team_to_code'] = donnees['team_to_code']
        global_model_data['team_global_stats'] = donnees['team_global_stats']
        global_model_data['precision'] = precision
        global_model_data['model'] = donnees['model']
        global_model_data['features'] = donnees['features']
        global_model_data['_tables_initialisees'] = True

        bot.reply_to(
            message,
            f"✅ *Modèle chargé !*\n"
            f"📊 {nb_matchs} matchs | 🎯 Précision : {round(precision * 100, 2)}%",
            parse_mode="Markdown"
        )
        _chargement_en_cours = False
        return True

    except Exception as e:
        print(f"❌ Erreur chargement cache : {e}")
        _chargement_en_cours = False
        return False


def _barre_progression(pct):
    rempli = int(round(pct / 10))
    if rempli > 10:
        rempli = 10
    if rempli < 0:
        rempli = 0
    return "█" * rempli + "░" * (10 - rempli)


def _formater_bulletin(resultat):
    h = resultat['home_team']
    a = resultat['away_team']
    p_h = resultat['p_h']
    p_d = resultat['p_d']
    p_a = resultat['p_a']

    dc_1x = resultat['dc_1x']
    dc_x2 = resultat['dc_x2']
    dc_12 = resultat['dc_12']

    meilleure_dc = max(
        [("1X", dc_1x, "Domicile ou Nul"),
         ("X2", dc_x2, "Nul ou Extérieur"),
         ("12", dc_12, "Pas de match nul")],
        key=lambda x: x[1]
    )

    max_p = max(p_h, p_d, p_a)
    if max_p >= 0.55:
        conf_emoji = "🟢"
        conf_txt = "ÉLEVÉE"
    elif max_p >= 0.45:
        conf_emoji = "🟡"
        conf_txt = "MODÉRÉE"
    else:
        conf_emoji = "🔴"
        conf_txt = "FAIBLE"

    top_scores = resultat.get('top_scores', [])
    scores_txt = ""
    medailles = ["🥇", "🥈", "🥉"]
    for i, (sh, sa, proba) in enumerate(top_scores[:3]):
        scores_txt += f"  {medailles[i]} *{sh} - {sa}* ➜ {round(proba*100, 1)}%\n"

    bulletin = (
        f"╔══════════════════════════╗\n"
        f"║  🏆 *PRONOSTIC FOOTBALL*  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"🏟️ *{h}* 🆚 *{a}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *RÉSULTAT 1N2*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏠 *{h}*\n"
        f"   `{_barre_progression(p_h*100)}` *{round(p_h*100,1)}%*\n"
        f"   💰 Cote : *{round(1/p_h, 2)}*\n\n"
        f"⚖️ *Match Nul*\n"
        f"   `{_barre_progression(p_d*100)}` *{round(p_d*100,1)}%*\n"
        f"   💰 Cote : *{round(1/p_d, 2)}*\n\n"
        f"✈️ *{a}*\n"
        f"   `{_barre_progression(p_a*100)}` *{round(p_a*100,1)}%*\n"
        f"   💰 Cote : *{round(1/p_a, 2)}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *DOUBLE CHANCE (paris sûrs)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• *1X* — {h} ou Nul\n"
        f"   `{_barre_progression(dc_1x*100)}` *{round(dc_1x*100,1)}%*\n\n"
        f"• *X2* — Nul ou {a}\n"
        f"   `{_barre_progression(dc_x2*100)}` *{round(dc_x2*100,1)}%*\n\n"
        f"• *12* — Pas de nul\n"
        f"   `{_barre_progression(dc_12*100)}` *{round(dc_12*100,1)}%*\n\n"
        f"💡 *Recommandé :* *{meilleure_dc[0]}* ({meilleure_dc[2]})\n"
        f"   Confiance : *{round(meilleure_dc[1]*100, 1)}%*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ *TENDANCES BUTS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 *Plus de 2.5 buts* :\n"
        f"   `{_barre_progression(resultat['over_25']*100)}` *{round(resultat['over_25']*100,1)}%*\n\n"
        f"📉 *Moins de 2.5 buts* :\n"
        f"   `{_barre_progression(resultat['under_25']*100)}` *{round(resultat['under_25']*100,1)}%*\n\n"
        f"✅ *Les 2 marquent* :\n"
        f"   `{_barre_progression(resultat['btts_yes']*100)}` *{round(resultat['btts_yes']*100,1)}%*\n\n"
        f"❌ *Pas les 2* :\n"
        f"   `{_barre_progression(resultat['btts_no']*100)}` *{round(resultat['btts_no']*100,1)}%*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *SCORES EXACTS PROBABLES*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{scores_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{conf_emoji} *Confiance globale : {conf_txt}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"_💡 Jouez de manière responsable._"
    )

    return bulletin


def enregistrer_handlers(bot):

    # =========================================================
    # /start et /help
    # =========================================================
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user

        if est_banni(user.id):
            bot.reply_to(message, "🚫 Tu es banni de ce bot.")
            return

        enregistrer_utilisateur(user.id, user.username, user.first_name)

        statut_label = get_statut_label(user.id)
        prec = global_model_data.get('precision', 0.5)
        nb_matchs = len(global_model_data.get('df', []))
        compteur = get_compteur_jour(user.id)
        limite = get_limite_jour(user.id)

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton("⚽ Faire un Pronostic"),
            telebot.types.KeyboardButton("📜 Historique"),
            telebot.types.KeyboardButton("📊 Statistiques du Modèle"),
            telebot.types.KeyboardButton("🔔 Notifications"),
            telebot.types.KeyboardButton("⭐ Passer Premium"),
        )

        welcome_text = (
            f"╔══════════════════════════╗\n"
            f"║   🤖 *ASSISTANT PRO*     ║\n"
            f"╚══════════════════════════╝\n\n"
            f"👋 Bienvenue *{user.first_name}* !\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Ton profil*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏅 Statut : *{statut_label}*\n"
            f"🎫 Pronostics : *{compteur}/{limite}*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 *Modèle IA*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Matchs analysés : *{nb_matchs}*\n"
            f"🎯 Précision : *{round(prec * 100, 2)}%*\n\n"
            "👇 *Choisis une option :*"
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)


    # =========================================================
    # /update
    # =========================================================
    @bot.message_handler(commands=['update'])
    def force_update_data(message):
        bot.reply_to(message, "⏳ Synchronisation en arrière-plan (1-2 min)...")
        threading.Thread(
            target=tache_arriere_plan_maj,
            args=(message.chat.id, bot),
            daemon=True
        ).start()


    # =========================================================
    # /myid
    # =========================================================
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        bot.reply_to(
            message,
            f"╔══════════════════════════╗\n"
            f"║      🆔 *TON ID*         ║\n"
            f"╚══════════════════════════╝\n\n"
            f"`{message.from_user.id}`",
            parse_mode="Markdown"
        )


    # =========================================================
    # /notif_on, /notif_off
    # =========================================================
    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        user_id = message.from_user.id
        if activer_notifications(user_id):
            bot.reply_to(
                message,
                f"🔔 *Notifications ACTIVÉES*\n\n"
                f"Tu recevras chaque matin à *8h* les meilleurs pronostics du jour.\n\n"
                f"_Pour désactiver : /notif_off_",
                parse_mode="Markdown"
            )


    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        user_id = message.from_user.id
        if desactiver_notifications(user_id):
            bot.reply_to(
                message,
                f"🔕 *Notifications DÉSACTIVÉES*\n\n"
                f"Tu ne recevras plus les notifications.\n\n"
                f"_Pour réactiver : /notif_on_",
                parse_mode="Markdown"
            )


    # =========================================================
    # /admin — Panneau admin principal
    # =========================================================
    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        user_id = message.from_user.id
        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée à l'administrateur.")
            return

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("📊 Stats", callback_data="admin|stats"),
            telebot.types.InlineKeyboardButton("👥 Utilisateurs", callback_data="admin|users"),
            telebot.types.InlineKeyboardButton("👑 Admins", callback_data="admin|admins"),
            telebot.types.InlineKeyboardButton("⚙️ Paramètres", callback_data="admin|params"),
            telebot.types.InlineKeyboardButton("📝 Logs", callback_data="admin|logs"),
            telebot.types.InlineKeyboardButton("🚫 Bannis", callback_data="admin|bannis"),
        )

        bot.reply_to(
            message,
            f"╔══════════════════════════╗\n"
            f"║   👑 *PANNEAU ADMIN*     ║\n"
            f"╚══════════════════════════╝\n\n"
            f"👇 *Que veux-tu faire ?*\n\n"
            f"*Commandes disponibles :*\n"
            f"/stats — Statistiques\n"
            f"/users — Liste utilisateurs\n"
            f"/broadcast msg — Annonce\n"
            f"/ban ID — Bannir\n"
            f"/unban ID — Débannir\n"
            f"/add_premium ID jours\n"
            f"/add_admin ID\n"
            f"/set_param cle valeur",
            parse_mode="Markdown",
            reply_markup=markup
        )


    # =========================================================
    # CALLBACKS ADMIN
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin|"))
    def traiter_admin_callback(call):
        user_id = call.from_user.id
        if not est_administrateur(user_id):
            bot.answer_callback_query(call.id, "⛔ Accès refusé.")
            return

        action = call.data.split("|")[1]
        bot.answer_callback_query(call.id, "⏳")

        if action == "stats":
            stats = get_stats_globales()
            bot.send_message(
                call.message.chat.id,
                f"╔══════════════════════════╗\n"
                f"║   📊 *STATISTIQUES*      ║\n"
                f"╚══════════════════════════╝\n\n"
                f"👥 *Total* : *{stats.get('total', 0)}*\n"
                f"⭐ *Premium* : *{stats.get('premium', 0)}*\n"
                f"🆓 *Free* : *{stats.get('free', 0)}*\n\n"
                f"📈 *Nouveaux (7j)* : *{stats.get('nouveaux_7j', 0)}*\n"
                f"📅 *Nouveaux (24h)* : *{stats.get('nouveaux_24h', 0)}*\n\n"
                f"🚫 *Bannis* : *{stats.get('bannis', 0)}*",
                parse_mode="Markdown"
            )

        elif action == "users":
            users = get_liste_utilisateurs(limite=20)
            texte = (
                f"╔══════════════════════════╗\n"
                f"║   👥 *UTILISATEURS*      ║\n"
                f"╚══════════════════════════╝\n\n"
            )
            for i, u in enumerate(users, 1):
                emoji = "⭐" if u['status'] == 'premium' else "🆓"
                texte += (
                    f"*{i}.* {emoji} *{u['first_name'] or 'Anonyme'}*\n"
                    f"   🆔 `{u['user_id']}`\n\n"
                )
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        elif action == "admins":
            admins = get_tous_admins()
            texte = (
                f"╔══════════════════════════╗\n"
                f"║     👑 *ADMINS*          ║\n"
                f"╚══════════════════════════╝\n\n"
                f"👑 *Principal* : `8653408729`\n\n"
            )
            for a in admins:
                texte += f"• `{a['user_id']}` — {a['nom'] or 'Sans nom'}\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        elif action == "params":
            params = get_tous_parametres()
            if not params:
                bot.send_message(call.message.chat.id, "Aucun paramètre défini. Utilise /set_param")
                return
            texte = (
                f"╔══════════════════════════╗\n"
                f"║   ⚙️ *PARAMÈTRES*        ║\n"
                f"╚══════════════════════════╝\n\n"
            )
            for p in params:
                texte += f"• `{p['cle']}` = *{p['valeur']}*\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        elif action == "logs":
            logs = get_logs_admin(limite=15)
            if not logs:
                bot.send_message(call.message.chat.id, "Aucun log pour l'instant.")
                return
            texte = (
                f"╔══════════════════════════╗\n"
                f"║     📝 *LOGS ADMIN*      ║\n"
                f"╚══════════════════════════╝\n\n"
            )
            for log in logs:
                texte += (
                    f"• `{log['action']}`\n"
                    f"  👤 {log['admin_id']}\n"
                    f"  📋 {log['details'][:50]}\n\n"
                )
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")

        elif action == "bannis":
            bannis = get_liste_bannis()
            if not bannis:
                bot.send_message(call.message.chat.id, "Aucun banni.")
                return
            texte = (
                f"╔══════════════════════════╗\n"
                f"║     🚫 *BANNIS*          ║\n"
                f"╚══════════════════════════╝\n\n"
            )
            for b in bannis:
                texte += f"• `{b['user_id']}` — {b['raison'] or 'Sans raison'}\n"
            bot.send_message(call.message.chat.id, texte, parse_mode="Markdown")


    # =========================================================
    # COMMANDES ADMIN RAPIDES
    # =========================================================
    @bot.message_handler(commands=['stats'])
    def cmd_stats(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        stats = get_stats_globales()
        bot.reply_to(
            message,
            f"📊 *Statistiques*\n\n"
            f"👥 Total : *{stats.get('total', 0)}*\n"
            f"⭐ Premium : *{stats.get('premium', 0)}*\n"
            f"🆓 Free : *{stats.get('free', 0)}*\n"
            f"📈 Nouveaux 7j : *{stats.get('nouveaux_7j', 0)}*\n"
            f"🚫 Bannis : *{stats.get('bannis', 0)}*",
            parse_mode="Markdown"
        )


    @bot.message_handler(commands=['users'])
    def cmd_users(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        users = get_liste_utilisateurs(limite=30)
        texte = f"👥 *30 derniers utilisateurs*\n\n"
        for i, u in enumerate(users, 1):
            emoji = "⭐" if u['status'] == 'premium' else "🆓"
            texte += f"{i}. {emoji} {u['first_name'] or '?'} — `{u['user_id']}`\n"
        bot.reply_to(message, texte, parse_mode="Markdown")


    @bot.message_handler(commands=['add_admin'])
    def cmd_add_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "📖 Usage : `/add_admin ID`", parse_mode="Markdown")
            return
        new_id = int(parts[1])
        if ajouter_admin(new_id):
            log_admin(message.from_user.id, "add_admin", f"ID: {new_id}")
            bot.reply_to(message, f"✅ Admin `{new_id}` ajouté.", parse_mode="Markdown")


    @bot.message_handler(commands=['remove_admin'])
    def cmd_remove_admin(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "📖 Usage : `/remove_admin ID`", parse_mode="Markdown")
            return
        target = int(parts[1])
        if retirer_admin(target):
            log_admin(message.from_user.id, "remove_admin", f"ID: {target}")
            bot.reply_to(message, f"✅ Admin `{target}` retiré.", parse_mode="Markdown")


    @bot.message_handler(commands=['ban'])
    def cmd_ban(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "📖 Usage : `/ban ID raison`", parse_mode="Markdown")
            return
        target = int(parts[1])
        raison = parts[2] if len(parts) > 2 else ""
        if bannir_user(target, raison):
            log_admin(message.from_user.id, "ban", f"ID: {target}")
            bot.reply_to(message, f"🚫 Utilisateur `{target}` banni.", parse_mode="Markdown")


    @bot.message_handler(commands=['unban'])
    def cmd_unban(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.reply_to(message, "📖 Usage : `/unban ID`", parse_mode="Markdown")
            return
        target = int(parts[1])
        if debannir_user(target):
            log_admin(message.from_user.id, "unban", f"ID: {target}")
            bot.reply_to(message, f"✅ Utilisateur `{target}` débanni.", parse_mode="Markdown")


    @bot.message_handler(commands=['add_premium'])
    def cmd_add_premium(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "📖 Usage : `/add_premium ID jours`", parse_mode="Markdown")
            return
        try:
            target = int(parts[1])
            jours = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ ID et jours doivent être des nombres.")
            return
        expiration = (datetime.now() + timedelta(days=jours)).strftime("%Y-%m-%d %H:%M")
        if set_premium(target, expiration):
            log_admin(message.from_user.id, "add_premium", f"ID: {target} - {jours}j")
            bot.reply_to(
                message,
                f"⭐ Utilisateur `{target}` PREMIUM pour *{jours} jours*\n"
                f"📅 Expire : {expiration}",
                parse_mode="Markdown"
            )
            try:
                bot.send_message(
                    target,
                    f"🎉 *Ton compte a été passé en PREMIUM !*\n\n"
                    f"⭐ Durée : *{jours} jours*\n"
                    f"📅 Expire : *{expiration}*",
                    parse_mode="Markdown"
                )
            except Exception:
                pass


    @bot.message_handler(commands=['set_param'])
    def cmd_set_param(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "📖 Usage : `/set_param cle valeur`", parse_mode="Markdown")
            return
        cle = parts[1]
        valeur = parts[2]
        if set_parametre(cle, valeur):
            log_admin(message.from_user.id, "set_param", f"{cle} = {valeur}")
            bot.reply_to(message, f"✅ `{cle}` = *{valeur}*", parse_mode="Markdown")


    @bot.message_handler(commands=['get_param'])
    def cmd_get_param(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "📖 Usage : `/get_param cle`", parse_mode="Markdown")
            return
        val = get_parametre(parts[1], "Non défini")
        bot.reply_to(message, f"`{parts[1]}` = *{val}*", parse_mode="Markdown")


    @bot.message_handler(commands=['broadcast'])
    def cmd_broadcast(message):
        if not est_administrateur(message.from_user.id):
            bot.reply_to(message, "⛔ Accès refusé.")
            return
        texte = message.text.replace("/broadcast", "").strip()
        if not texte:
            bot.reply_to(message, "📖 Usage : `/broadcast ton message`", parse_mode="Markdown")
            return

        users = get_tous_utilisateurs()
        succes = 0
        echecs = 0
        for uid in users:
            try:
                bot.send_message(
                    uid,
                    f"📢 *ANNONCE ADMIN*\n\n{texte}",
                    parse_mode="Markdown"
                )
                succes += 1
                time.sleep(0.05)
            except Exception:
                echecs += 1

        log_admin(message.from_user.id, "broadcast", f"{succes} ok, {echecs} échecs")
        bot.reply_to(
            message,
            f"✅ *Broadcast terminé*\n\n"
            f"📤 Envoyés : *{succes}*\n"
            f"❌ Échecs : *{echecs}*",
            parse_mode="Markdown"
        )


    # =========================================================
    # CALLBACK NOTIFS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("notif|"))
    def traiter_notif_callback(call):
        user_id = call.from_user.id
        action = call.data.split("|")[1]

        if action == "on":
            if activer_notifications(user_id):
                bot.answer_callback_query(call.id, "✅ Notifications activées !")
                bot.send_message(
                    call.message.chat.id,
                    "🔔 *Notifications ACTIVÉES*\n\nTu recevras les pronostics chaque matin à 8h.",
                    parse_mode="Markdown"
                )
        elif action == "off":
            if desactiver_notifications(user_id):
                bot.answer_callback_query(call.id, "🔕 Désactivées")
                bot.send_message(
                    call.message.chat.id,
                    "🔕 *Notifications DÉSACTIVÉES*",
                    parse_mode="Markdown"
                )


    # =========================================================
    # MENU PRINCIPAL
    # =========================================================
    @bot.message_handler(func=lambda message: True)
    def handle_menu_clicks(message):
        text = message.text
        user_id = message.from_user.id

        if est_banni(user_id):
            bot.reply_to(message, "🚫 Tu es banni de ce bot.")
            return

        if text == "📊 Statistiques du Modèle":
            prec = global_model_data.get('precision', 0.5)
            length = len(global_model_data.get('df', []))
            bot.reply_to(
                message,
                f"📊 *Statistiques IA*\n\n"
                f"📈 Matchs analysés : *{length}*\n"
                f"🎯 Précision : *{round(prec * 100, 2)}%*\n"
                f"⚙️ Algorithme : *RF + GB*\n"
                f"📊 Features : *30 variables*",
                parse_mode="Markdown"
            )

        elif text == "📜 Historique":
            try:
                import pandas as pd
                hist = pd.read_csv(FICHIER_HISTORIQUE)
                last_5 = hist.tail(5)
                texte = "📜 *Tes 5 derniers pronostics*\n\n"
                for i, (_, row) in enumerate(last_5.iterrows(), 1):
                    texte += (
                        f"*{i}.* ⚽ {row['Match']}\n"
                        f"   📅 {row['Date_Consultation']}\n"
                        f"   💡 {row['Pronostic_1N2']}\n"
                        f"   🎯 Score : {row['Score_Exact']}\n\n"
                    )
                bot.reply_to(message, texte, parse_mode="Markdown")
            except FileNotFoundError:
                bot.reply_to(message, "⚠️ Aucun historique pour l'instant.")

        elif text == "🔔 Notifications":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("🔔 Activer", callback_data="notif|on"),
                telebot.types.InlineKeyboardButton("🔕 Désactiver", callback_data="notif|off"),
            )
            bot.reply_to(
                message,
                f"🔔 *Notifications*\n\n"
                f"📬 Chaque matin à *8h*, tu recevras les *3 meilleurs pronostics du jour*.\n\n"
                f"👉 Choisis une option :",
                parse_mode="Markdown",
                reply_markup=markup
            )

        elif text == "⭐ Passer Premium":
            if est_premium(user_id):
                bot.reply_to(
                    message,
                    f"✅ *Tu es déjà Premium !*\n\nProfite bien de tes pronostics illimités 🚀",
                    parse_mode="Markdown"
                )
                return
            bot.reply_to(
                message,
                f"⭐ *Abonnement Premium*\n\n"
                f"🎁 *Avantages :*\n"
                f"  • ♾️ Pronostics illimités\n"
                f"  • 🎯 Score exact + Over/BTTS\n"
                f"  • 💬 Support prioritaire\n\n"
                f"💳 *Formules :*\n"
                f"📅 Journalier : *2 000 CDF*\n"
                f"📆 Hebdomadaire : *6 000 CDF*\n"
                f"🗓️ Mensuel : *10 000 CDF*\n\n"
                f"📲 _Paiement : Mobile Money_\n"
                f"_Bientôt disponible..._",
                parse_mode="Markdown"
            )

        elif text == "⚽ Faire un Pronostic":
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                    f"⭐ Passe en *Premium* !",
                    parse_mode="Markdown"
                )
                return
            bot.reply_to(
                message,
                f"✍️ *Tape l'affiche du match :*\n\n"
                f"`EquipeDom vs EquipeExt`\n\n"
                f"💡 Exemples :\n"
                f"  • `psg vs marseille`\n"
                f"  • `barca vs real`",
                parse_mode="Markdown"
            )

        elif 'vs' in text.lower():
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                    "Passe en ⭐ *Premium* !",
                    parse_mode="Markdown"
                )
                return

            parts = text.split('vs' if 'vs' in text else 'VS')
            if len(parts) < 2:
                bot.reply_to(message, "📖 Format : `Equipe A vs Equipe B`", parse_mode="Markdown")
                return

            resultat = predire_match(parts[0].strip(), parts[1].strip())

            if "erreur" in resultat:
                bot.reply_to(
                    message,
                    f"❌ *{resultat['erreur']}*\n\n"
                    f"💡 Essaie : `psg vs marseille`",
                    parse_mode="Markdown"
                )
                return

            bulletin = _formater_bulletin(resultat)
            bot.reply_to(message, bulletin, parse_mode="Markdown")

            sauvegarder_historique(
                resultat['home_team'], resultat['away_team'],
                resultat['p_h'], resultat['p_d'], resultat['p_a'],
                resultat['best_score'][0], resultat['best_score'][1]
            )

            incrementer_compteur(user_id)

        else:
            bot.reply_to(
                message,
                "💡 *Utilise les boutons du menu.*\n\n"
                "Ou tape : `Equipe A vs Equipe B`",
                parse_mode="Markdown"
            )
