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
    est_banni,
    get_langue, set_langue
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.ml_model import global_model_data, tache_arriere_plan_maj
from core.prediction import predire_match, sauvegarder_historique


_chargement_en_cours = False


def _charger_modele_si_necessaire(message, bot):
    global _chargement_en_cours

    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True

    if _chargement_en_cours:
        bot.reply_to(message, "Chargement en cours...")
        return False

    _chargement_en_cours = True

    try:
        cache = charger_modele_cache()
        if not cache:
            bot.reply_to(message, "Aucun modele en cache.")
            _chargement_en_cours = False
            return False

        modele_bytes, precision, nb_matchs = cache
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

        _chargement_en_cours = False
        return True

    except Exception as e:
        print(f"Erreur chargement cache : {e}")
        _chargement_en_cours = False
        return False


def _formater_bulletin(resultat, langue="fr"):
    h = resultat['home_team']
    a = resultat['away_team']
    p_h = resultat['p_h']
    p_d = resultat['p_d']
    p_a = resultat['p_a']
    dc_1x = resultat['dc_1x']
    dc_x2 = resultat['dc_x2']
    dc_12 = resultat['dc_12']

    meilleure_dc = max(
        [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)],
        key=lambda x: x[1]
    )

    titres = {
        "fr": {"bulletin": "PRONOSTIC FOOTBALL", "res": "RESULTAT 1N2", "nul": "Match nul",
               "dc": "DOUBLE CHANCE", "reco": "Recommandation", "buts": "TENDANCES BUTS",
               "plus": "Plus de 2.5 buts", "moins": "Moins de 2.5 buts",
               "btts_oui": "Les 2 marquent", "btts_non": "Pas les 2",
               "scores": "SCORES PROBABLES", "resp": "Jouez de maniere responsable."},
        "en": {"bulletin": "FOOTBALL PREDICTION", "res": "1X2 RESULT", "nul": "Draw",
               "dc": "DOUBLE CHANCE", "reco": "Recommended", "buts": "GOALS TRENDS",
               "plus": "Over 2.5 goals", "moins": "Under 2.5 goals",
               "btts_oui": "Both teams score", "btts_non": "Not both",
               "scores": "PROBABLE SCORES", "resp": "Play responsibly."},
        "ln": {"bulletin": "BOKANO YA MASANO", "res": "RESULTAT 1N2", "nul": "Ekoki",
               "dc": "DOUBLE CHANCE", "reco": "Malako", "buts": "BIKOKISI",
               "plus": "Eleki 2.5", "moins": "Ekiti 2.5",
               "btts_oui": "Bapayi nyonso", "btts_non": "Bapayi nyonso te",
               "scores": "BIKOKISI", "resp": "Sala yango malamu."},
    }

    t = titres.get(langue, titres["fr"])

    scores_txt = ""
    for i, (sh, sa, proba) in enumerate(resultat.get('top_scores', [])[:3], 1):
        scores_txt += f"{i}. {sh} - {sa} : {round(proba*100, 1)}%\n"

    return (
        f"{t['bulletin']}\n"
        f"========================\n\n"
        f"{h} vs {a}\n\n"
        f"{t['res']}\n"
        f"------------------------\n"
        f"{h} : {round(p_h*100,1)}% ({round(1/p_h, 2)})\n"
        f"{t['nul']} : {round(p_d*100,1)}% ({round(1/p_d, 2)})\n"
        f"{a} : {round(p_a*100,1)}% ({round(1/p_a, 2)})\n\n"
        f"{t['dc']}\n"
        f"------------------------\n"
        f"1X : {round(dc_1x*100,1)}%\n"
        f"X2 : {round(dc_x2*100,1)}%\n"
        f"12 : {round(dc_12*100,1)}%\n\n"
        f"{t['reco']} : {meilleure_dc[0]} a {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"{t['buts']}\n"
        f"------------------------\n"
        f"{t['plus']} : {round(resultat['over_25']*100,1)}%\n"
        f"{t['moins']} : {round(resultat['under_25']*100,1)}%\n"
        f"{t['btts_oui']} : {round(resultat['btts_yes']*100,1)}%\n"
        f"{t['btts_non']} : {round(resultat['btts_no']*100,1)}%\n\n"
        f"{t['scores']}\n"
        f"------------------------\n"
        f"{scores_txt}\n"
        f"{t['resp']}"
    )


def enregistrer_handlers(bot):

    # =========================================================
    # /start
    # =========================================================
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user

        if est_banni(user.id):
            bot.reply_to(message, get_text("banni", get_langue(user.id)))
            return

        enregistrer_utilisateur(user.id, user.username, user.first_name)

        langue = get_langue(user.id)
        statut_label = get_statut_label(user.id)
        prec = global_model_data.get('precision', 0.5)
        nb_matchs = len(global_model_data.get('df', []))
        compteur = get_compteur_jour(user.id)
        limite = get_limite_jour(user.id)

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            telebot.types.KeyboardButton(get_text("btn_pronostic", langue)),
            telebot.types.KeyboardButton(get_text("btn_historique", langue)),
            telebot.types.KeyboardButton(get_text("btn_stats", langue)),
            telebot.types.KeyboardButton(get_text("btn_notifs", langue)),
            telebot.types.KeyboardButton(get_text("btn_premium", langue)),
            telebot.types.KeyboardButton(get_text("btn_langue", langue)),
        )

        welcome_text = get_text(
            "welcome", langue,
            nom=user.first_name,
            statut=statut_label,
            compteur=compteur,
            limite=limite,
            nb_matchs=nb_matchs,
            precision=round(prec * 100, 2)
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


    # =========================================================
    # /update
    # =========================================================
    @bot.message_handler(commands=['update'])
    def force_update_data(message):
        bot.reply_to(message, "Synchronisation en arriere-plan...")
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
        bot.reply_to(message, f"ID : {message.from_user.id}")


    # =========================================================
    # /langue (commande directe)
    # =========================================================
    @bot.message_handler(commands=['langue', 'language'])
    def cmd_langue(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for code, nom in LANGUES_DISPONIBLES.items():
            markup.add(telebot.types.InlineKeyboardButton(
                nom,
                callback_data=f"lang|{code}"
            ))

        bot.reply_to(
            message,
            get_text("choix_langue", langue),
            reply_markup=markup
        )


    # =========================================================
    # CALLBACK LANGUE
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        user_id = call.from_user.id
        langue = call.data.split("|")[1]

        if set_langue(user_id, langue):
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(
                call.message.chat.id,
                get_text("langue_changee", langue)
            )
        else:
            bot.answer_callback_query(call.id, "Erreur")


    # =========================================================
    # /notif_on, /notif_off
    # =========================================================
    @bot.message_handler(commands=['notif_on'])
    def cmd_notif_on(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if activer_notifications(user_id):
            bot.reply_to(message, get_text("notifs_activees", langue))


    @bot.message_handler(commands=['notif_off'])
    def cmd_notif_off(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        if desactiver_notifications(user_id):
            bot.reply_to(message, get_text("notifs_desactivees", langue))


    # =========================================================
    # CALLBACK NOTIFS
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("notif|"))
    def traiter_notif_callback(call):
        user_id = call.from_user.id
        langue = get_langue(user_id)
        action = call.data.split("|")[1]

        if action == "on":
            if activer_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_activees", langue))
        elif action == "off":
            if desactiver_notifications(user_id):
                bot.answer_callback_query(call.id, "OK")
                bot.send_message(call.message.chat.id, get_text("notifs_desactivees", langue))


    # =========================================================
    # MENU PRINCIPAL (fallback - TOUJOURS EN DERNIER)
    # =========================================================
    @bot.message_handler(func=lambda message: True)
    def handle_menu_clicks(message):
        text = message.text
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        # Statistiques
        if text == get_text("btn_stats", langue):
            prec = global_model_data.get('precision', 0.5)
            length = len(global_model_data.get('df', []))
            bot.reply_to(
                message,
                get_text("stats_ia", langue, nb_matchs=length, precision=round(prec * 100, 2))
            )

        # Historique
        elif text == get_text("btn_historique", langue):
            try:
                import pandas as pd
                hist = pd.read_csv(FICHIER_HISTORIQUE)
                last_5 = hist.tail(5)
                texte = get_text("historique_titre", langue)
                for i, (_, row) in enumerate(last_5.iterrows(), 1):
                    texte += (
                        f"{i}. {row['Match']}\n"
                        f"   {row['Date_Consultation']}\n"
                        f"   {row['Pronostic_1N2']}\n"
                        f"   Score : {row['Score_Exact']}\n\n"
                    )
                bot.reply_to(message, texte)
            except FileNotFoundError:
                bot.reply_to(message, get_text("historique_vide", langue))

        # Notifications
        elif text == get_text("btn_notifs", langue):
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    get_text("bouton_activer", langue),
                    callback_data="notif|on"
                ),
                telebot.types.InlineKeyboardButton(
                    get_text("bouton_desactiver", langue),
                    callback_data="notif|off"
                ),
            )
            bot.reply_to(
                message,
                get_text("notifs_titre", langue),
                reply_markup=markup
            )

        # Langue
        elif text == get_text("btn_langue", langue):
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for code, nom in LANGUES_DISPONIBLES.items():
                markup.add(telebot.types.InlineKeyboardButton(
                    nom,
                    callback_data=f"lang|{code}"
                ))
            bot.reply_to(
                message,
                get_text("choix_langue", langue),
                reply_markup=markup
            )

        # Premium
        elif text == get_text("btn_premium", langue):
            if est_premium(user_id):
                bot.reply_to(message, get_text("premium_actif", langue))
                return
            bot.reply_to(message, get_text("premium_titre", langue))

        # Faire un Pronostic
        elif text == get_text("btn_pronostic", langue):
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
                )
                return
            bot.reply_to(message, get_text("demande_affiche", langue))

        # Prédiction
        elif 'vs' in text.lower():
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
                )
                return

            parts = text.split('vs' if 'vs' in text else 'VS')
            if len(parts) < 2:
                bot.reply_to(message, get_text("demande_affiche", langue))
                return

            resultat = predire_match(parts[0].strip(), parts[1].strip())

            if "erreur" in resultat:
                bot.reply_to(message, get_text("erreur_equipe", langue, erreur=resultat['erreur']))
                return

            bulletin = _formater_bulletin(resultat, langue)
            bot.reply_to(message, bulletin)

            sauvegarder_historique(
                resultat['home_team'], resultat['away_team'],
                resultat['p_h'], resultat['p_d'], resultat['p_a'],
                resultat['best_score'][0], resultat['best_score'][1]
            )

            incrementer_compteur(user_id)

        else:
            bot.reply_to(message, get_text("fallback", langue))
