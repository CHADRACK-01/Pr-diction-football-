import threading
import io
import joblib
import telebot

from config import FICHIER_HISTORIQUE
from users import (
    enregistrer_utilisateur, get_statut_label, peut_faire_pronostic,
    get_compteur_jour, get_limite_jour, incrementer_compteur, est_premium,
    charger_modele_cache,
    activer_notifications, desactiver_notifications,
    est_banni
)
from core.ml_model import global_model_data, tache_arriere_plan_maj
from core.prediction import predire_match, sauvegarder_historique


_chargement_en_cours = False


def _charger_modele_si_necessaire(message, bot):
    global _chargement_en_cours

    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True

    if _chargement_en_cours:
        bot.reply_to(message, "Chargement en cours, patiente...")
        return False

    _chargement_en_cours = True

    try:
        cache = charger_modele_cache()
        if not cache:
            bot.reply_to(message, "Aucun modele en cache. Contacte l'administrateur.")
            _chargement_en_cours = False
            return False

        modele_bytes, precision, nb_matchs = cache
        print(f"Chargement du cache ({nb_matchs} matchs, precision={round(precision*100, 2)}%)...")

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
            f"Modele charge !\n"
            f"{nb_matchs} matchs | Precision : {round(precision * 100, 2)}%"
        )
        _chargement_en_cours = False
        return True

    except Exception as e:
        print(f"Erreur chargement cache : {e}")
        _chargement_en_cours = False
        return False


def _barre_progression(pct):
    rempli = int(round(pct / 10))
    if rempli > 10:
        rempli = 10
    if rempli < 0:
        rempli = 0
    return "#" * rempli + "." * (10 - rempli)


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
         ("X2", dc_x2, "Nul ou Exterieur"),
         ("12", dc_12, "Pas de match nul")],
        key=lambda x: x[1]
    )

    max_p = max(p_h, p_d, p_a)
    if max_p >= 0.55:
        conf_txt = "ELEVEE"
    elif max_p >= 0.45:
        conf_txt = "MODEREE"
    else:
        conf_txt = "FAIBLE"

    top_scores = resultat.get('top_scores', [])
    scores_txt = ""
    for i, (sh, sa, proba) in enumerate(top_scores[:3], 1):
        scores_txt += f"{i}. {sh} - {sa} : {round(proba*100, 1)}%\n"

    bulletin = (
        f"PRONOSTIC FOOTBALL\n"
        f"========================\n\n"
        f"{h} vs {a}\n\n"
        f"RESULTAT 1N2\n"
        f"------------------------\n"
        f"{h} : {round(p_h*100,1)}% (cote {round(1/p_h, 2)})\n"
        f"Match nul : {round(p_d*100,1)}% (cote {round(1/p_d, 2)})\n"
        f"{a} : {round(p_a*100,1)}% (cote {round(1/p_a, 2)})\n\n"
        f"DOUBLE CHANCE\n"
        f"------------------------\n"
        f"1X ({h} ou Nul) : {round(dc_1x*100,1)}%\n"
        f"X2 (Nul ou {a}) : {round(dc_x2*100,1)}%\n"
        f"12 (Pas de nul) : {round(dc_12*100,1)}%\n\n"
        f"Recommandation : {meilleure_dc[0]} ({meilleure_dc[2]}) a {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"TENDANCES BUTS\n"
        f"------------------------\n"
        f"Plus de 2.5 buts : {round(resultat['over_25']*100,1)}%\n"
        f"Moins de 2.5 buts : {round(resultat['under_25']*100,1)}%\n"
        f"Les 2 marquent : {round(resultat['btts_yes']*100,1)}%\n"
        f"Pas les 2 : {round(resultat['btts_no']*100,1)}%\n\n"
        f"SCORES PROBABLES\n"
        f"------------------------\n"
        f"{scores_txt}\n"
        f"Confiance globale : {conf_txt}\n\n"
        f"Jouez de maniere responsable."
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
            bot.reply_to(message, "Tu es banni de ce bot.")
            return

        enregistrer_utilisateur(user.id, user.username, user.first_name)

        statut_label = get_statut_label(user.id)
        prec = global_model_data.get('precision', 0.5)
        nb_matchs = len(global_model_data.get('df', []))
        compteur = get_compteur_jour(user.id)
        limite = get_limite_jour(user.id)

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton("Faire un Pronostic"),
            telebot.types.KeyboardButton("Historique"),
            telebot.types.KeyboardButton("Statistiques"),
            telebot.types.KeyboardButton("Notifications"),
            telebot.types.KeyboardButton("Passer Premium"),
        )

        welcome_text = (
            f"ASSISTANT PRO\n\n"
            f"Bienvenue {user.first_name} !\n\n"
            f"Statut : {statut_label}\n"
            f"Pronostics : {compteur}/{limite}\n\n"
            f"Matchs analyses : {nb_matchs}\n"
            f"Precision : {round(prec * 100, 2)}%\n\n"
            f"Choisis une option :"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


    # =========================================================
    # /update
    # =========================================================
    @bot.message_handler(commands=['update'])
    def force_update_data(message):
        bot.reply_to(message, "Synchronisation en arriere-plan (1-2 min)...")
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
        bot.reply_to(message, f"Ton ID : {message.from_user.id}")


    # =========================================================
    # /notif_on, /notif_off
    # =========================================================
    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        if activer_notifications(message.from_user.id):
            bot.reply_to(
                message,
                "Notifications ACTIVEES\n\nTu recevras chaque matin a 8h les meilleurs pronostics."
            )


    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        if desactiver_notifications(message.from_user.id):
            bot.reply_to(
                message,
                "Notifications DESACTIVEES\n\nTu ne recevras plus les notifications."
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
                bot.answer_callback_query(call.id, "Notifications activees")
                bot.send_message(call.message.chat.id, "Notifications ACTIVEES")
        elif action == "off":
            if desactiver_notifications(user_id):
                bot.answer_callback_query(call.id, "Notifications desactivees")
                bot.send_message(call.message.chat.id, "Notifications DESACTIVEES")


    # =========================================================
    # MENU PRINCIPAL
    # =========================================================
    @bot.message_handler(func=lambda message: True)
    def handle_menu_clicks(message):
        text = message.text
        user_id = message.from_user.id

        if est_banni(user_id):
            bot.reply_to(message, "Tu es banni de ce bot.")
            return

        # Statistiques
        if text == "Statistiques":
            prec = global_model_data.get('precision', 0.5)
            length = len(global_model_data.get('df', []))
            bot.reply_to(
                message,
                f"Statistiques IA\n\n"
                f"Matchs analyses : {length}\n"
                f"Precision : {round(prec * 100, 2)}%"
            )

        # Historique
        elif text == "Historique":
            try:
                import pandas as pd
                hist = pd.read_csv(FICHIER_HISTORIQUE)
                last_5 = hist.tail(5)
                texte = "Tes 5 derniers pronostics\n\n"
                for i, (_, row) in enumerate(last_5.iterrows(), 1):
                    texte += (
                        f"{i}. {row['Match']}\n"
                        f"   {row['Date_Consultation']}\n"
                        f"   {row['Pronostic_1N2']}\n"
                        f"   Score : {row['Score_Exact']}\n\n"
                    )
                bot.reply_to(message, texte)
            except FileNotFoundError:
                bot.reply_to(message, "Aucun historique pour l'instant.")

        # Notifications
        elif text == "Notifications":
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton("Activer", callback_data="notif|on"),
                telebot.types.InlineKeyboardButton("Desactiver", callback_data="notif|off"),
            )
            bot.reply_to(
                message,
                "Notifications\n\n"
                "Chaque matin a 8h, tu recevras les 3 meilleurs pronostics.\n\n"
                "Choisis une option :",
                reply_markup=markup
            )

        # Passer Premium
        elif text == "Passer Premium":
            if est_premium(user_id):
                bot.reply_to(message, "Tu es deja Premium !")
                return
            bot.reply_to(
                message,
                "Abonnement Premium\n\n"
                "Avantages :\n"
                "- Pronostics illimites\n"
                "- Score exact + Over/BTTS\n"
                "- Support prioritaire\n\n"
                "Formules :\n"
                "Journalier : 2 000 CDF\n"
                "Hebdomadaire : 6 000 CDF\n"
                "Mensuel : 10 000 CDF\n\n"
                "Paiement : Mobile Money (bientot disponible)"
            )

        # Faire un Pronostic
        elif text == "Faire un Pronostic":
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"Limite atteinte ({get_limite_jour(user_id)}/jour).\n\n"
                    f"Passe en Premium pour des pronostics illimites !"
                )
                return
            bot.reply_to(
                message,
                "Tape l'affiche du match :\n\n"
                "EquipeDom vs EquipeExt\n\n"
                "Exemples :\n"
                "psg vs marseille\n"
                "barca vs real"
            )

        # Prédiction
        elif 'vs' in text.lower():
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"Limite atteinte ({get_limite_jour(user_id)}/jour).\n\n"
                    "Passe en Premium !"
                )
                return

            parts = text.split('vs' if 'vs' in text else 'VS')
            if len(parts) < 2:
                bot.reply_to(message, "Format : Equipe A vs Equipe B")
                return

            resultat = predire_match(parts[0].strip(), parts[1].strip())

            if "erreur" in resultat:
                bot.reply_to(
                    message,
                    f"Erreur : {resultat['erreur']}\n\n"
                    f"Essaie : psg vs marseille"
                )
                return

            bulletin = _formater_bulletin(resultat)
            bot.reply_to(message, bulletin)

            sauvegarder_historique(
                resultat['home_team'], resultat['away_team'],
                resultat['p_h'], resultat['p_d'], resultat['p_a'],
                resultat['best_score'][0], resultat['best_score'][1]
            )

            incrementer_compteur(user_id)

        else:
            bot.reply_to(
                message,
                "Utilise les boutons du menu.\n\n"
                "Ou tape : Equipe A vs Equipe B"
            )
