import threading
import io
import joblib
import telebot
from datetime import datetime, timedelta

from config import FICHIER_HISTORIQUE
from users import (
    enregistrer_utilisateur, get_statut_label, peut_faire_pronostic,
    get_compteur_jour, get_limite_jour, incrementer_compteur, est_premium,
    charger_modele_cache,
    activer_notifications, desactiver_notifications,
    est_banni,
    get_langue, set_langue,
    get_user_info,
    set_premium,
    est_administrateur
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.payments import ABONNEMENTS, envoyer_facture
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
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


def _envoyer_menu_principal(chat_id, user_id, bot):
    langue = get_langue(user_id)
    statut_label = get_statut_label(user_id)
    prec = global_model_data.get('precision', 0.5)
    nb_matchs = len(global_model_data.get('df', []))
    compteur = get_compteur_jour(user_id)
    limite = get_limite_jour(user_id)

    user_info = get_user_info(user_id)
    nom = user_info['first_name'] if user_info else "Utilisateur"

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton(get_text("btn_pronostic", langue)),
        telebot.types.KeyboardButton(get_text("btn_matchs_jour", langue)),
        telebot.types.KeyboardButton(get_text("btn_historique", langue)),
        telebot.types.KeyboardButton(get_text("btn_stats", langue)),
        telebot.types.KeyboardButton(get_text("btn_notifs", langue)),
        telebot.types.KeyboardButton(get_text("btn_premium", langue)),
        telebot.types.KeyboardButton(get_text("btn_langue", langue)),
    )

    if est_administrateur(user_id):
        markup.add(telebot.types.KeyboardButton("Panneau Admin"))

    welcome_text = get_text(
        "welcome", langue,
        nom=nom,
        statut=statut_label,
        compteur=compteur,
        limite=limite,
        nb_matchs=nb_matchs,
        precision=round(prec * 100, 2)
    )

    bot.send_message(chat_id, welcome_text, reply_markup=markup)


def enregistrer_handlers(bot):

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user

        if est_banni(user.id):
            bot.reply_to(message, get_text("banni", get_langue(user.id)))
            return

        enregistrer_utilisateur(user.id, user.username, user.first_name)
        _envoyer_menu_principal(message.chat.id, user.id, bot)


    @bot.message_handler(commands=['update'])
    def force_update_data(message):
        bot.reply_to(message, "Synchronisation en arriere-plan...")
        threading.Thread(
            target=tache_arriere_plan_maj,
            args=(message.chat.id, bot),
            daemon=True
        ).start()


    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        bot.reply_to(message, f"ID : {message.from_user.id}")


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
            _envoyer_menu_principal(call.message.chat.id, user_id, bot)
        else:
            bot.answer_callback_query(call.id, "Erreur")


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


    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy|"))
    def traiter_achat(call):
        user_id = call.from_user.id
        abo_key = call.data.split("|")[1]

        if abo_key not in ABONNEMENTS:
            bot.answer_callback_query(call.id, "Formule inconnue.")
            return

        abo = ABONNEMENTS[abo_key]
        bot.answer_callback_query(call.id, f"{abo['nom']}")

        envoyer_facture(bot, call.message.chat.id, abo_key, user_id)


    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout(pre_checkout_query):
        try:
            bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        except Exception as e:
            print(f"Erreur pre_checkout : {e}")


    @bot.message_handler(content_types=['successful_payment'])
    def process_successful_payment(message):
        try:
            payment = message.successful_payment
            user_id = message.from_user.id
            payload = payment.invoice_payload

            parts = payload.split("_")
            abo_key = parts[1] if len(parts) >= 2 else "mensuel"

            if abo_key not in ABONNEMENTS:
                abo_key = "mensuel"

            abo = ABONNEMENTS[abo_key]
            duree = abo["duree_jours"]
            nom_abo = abo["nom"]

            expiration = (datetime.now() + timedelta(days=duree)).strftime("%Y-%m-%d %H:%M")
            set_premium(user_id, expiration)

            langue = get_langue(user_id)

            if langue == "en":
                texte = (
                    f"PAYMENT CONFIRMED\n\n"
                    f"Plan: {nom_abo}\n"
                    f"Duration: {duree} day(s)\n"
                    f"Expires: {expiration}\n\n"
                    f"Enjoy your unlimited predictions!"
                )
            elif langue == "ln":
                texte = (
                    f"MBONGO EZALI\n\n"
                    f"Formule: {nom_abo}\n"
                    f"Duree: {duree} mokolo\n"
                    f"Ekosila: {expiration}\n\n"
                    f"Kende na bokano!"
                )
            else:
                texte = (
                    f"PAIEMENT CONFIRME\n\n"
                    f"Formule : {nom_abo}\n"
                    f"Duree : {duree} jour(s)\n"
                    f"Expire : {expiration}\n\n"
                    f"Profite de tes pronostics illimites !"
                )

            bot.send_message(user_id, texte)
            print(f"Paiement Stars valide : user {user_id} - {nom_abo} - {payment.total_amount} Stars")

        except Exception as e:
            print(f"Erreur traitement paiement : {e}")
            bot.send_message(message.chat.id, f"Erreur : {str(e)}")


    @bot.message_handler(func=lambda message: True)
    def handle_menu_clicks(message):
        text = message.text
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        # Matchs du jour (avec DEBUG)
        if text == get_text("btn_matchs_jour", langue):
            if not _charger_modele_si_necessaire(message, bot):
                return

            bot.reply_to(message, "Recherche des matchs du jour...")

            try:
                print("=== DEBUG MATCHS DU JOUR ===")
                matchs = get_matchs_du_jour()
                print(f"Matchs trouves : {len(matchs)}")

                texte = formater_matchs_du_jour(matchs, langue)
                print(f"Texte formate : {len(texte)} caracteres")

                bot.send_message(message.chat.id, texte)
                print("Message envoye avec succes")
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"ERREUR MATCHS DU JOUR :\n{tb}")
                # Envoyer seulement les 800 derniers caractères
                bot.send_message(
                    message.chat.id,
                    f"Erreur : {str(e)[:200]}\n\nTraceback (fin) :\n{tb[-800:]}"
                )

        # Statistiques
        elif text == get_text("btn_stats", langue):
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

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    f"Journalier - {ABONNEMENTS['journalier']['prix_stars']} Stars",
                    callback_data="buy|journalier"
                ),
                telebot.types.InlineKeyboardButton(
                    f"Hebdomadaire - {ABONNEMENTS['hebdomadaire']['prix_stars']} Stars",
                    callback_data="buy|hebdomadaire"
                ),
                telebot.types.InlineKeyboardButton(
                    f"Mensuel - {ABONNEMENTS['mensuel']['prix_stars']} Stars",
                    callback_data="buy|mensuel"
                ),
            )

            bot.reply_to(
                message,
                get_text("premium_titre", langue),
                reply_markup=markup
            )

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

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Choisir avec des boutons",
                    callback_data="start_inline_prono"
                )
            )
            bot.reply_to(
                message,
                get_text("demande_affiche", langue),
                reply_markup=markup
            )

        # Prédiction par texte
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
