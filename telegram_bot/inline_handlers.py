import telebot

from users import get_langue, peut_faire_pronostic, get_limite_jour, incrementer_compteur
from core.ml_model import global_model_data
from core.prediction import predire_match, sauvegarder_historique
from core.translations import get_text


# Stockage temporaire des sélections en cours : {user_id: {"home": "Paris SG"}}
SESSIONS = {}


def _liste_equipes_par_lettre(lettre=None):
    """Retourne la liste des équipes, filtrées par lettre si fournie."""
    if not global_model_data or not global_model_data.get('teams'):
        return []

    teams = sorted(global_model_data['teams'])

    if lettre:
        teams = [t for t in teams if t.lower().startswith(lettre.lower())]

    return teams


def _clavier_lettres():
    """Crée un clavier inline avec les lettres A-Z."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=7)
    boutons = []
    for lettre in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        boutons.append(telebot.types.InlineKeyboardButton(
            lettre,
            callback_data=f"eq_letter|{lettre}"
        ))
    markup.add(*boutons)
    return markup


def _clavier_equipes(equipes, prefixe, page=0, taille=8):
    """Crée un clavier inline paginé avec les équipes."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)

    debut = page * taille
    fin = debut + taille
    equipes_page = equipes[debut:fin]

    for eq in equipes_page:
        markup.add(telebot.types.InlineKeyboardButton(
            eq,
            callback_data=f"{prefixe}|{eq}"
        ))

    # Navigation
    nav = []
    if page > 0:
        nav.append(telebot.types.InlineKeyboardButton(
            "<< Precedent",
            callback_data=f"page|{prefixe}|{page-1}"
        ))
    if fin < len(equipes):
        nav.append(telebot.types.InlineKeyboardButton(
            "Suivant >>",
            callback_data=f"page|{prefixe}|{page+1}"
        ))
    if nav:
        markup.add(*nav)

    # Bouton annuler
    markup.add(telebot.types.InlineKeyboardButton(
        "Annuler",
        callback_data="cancel_prono"
    ))

    return markup


def _formater_bulletin(resultat, langue="fr"):
    """Réutilise le même format que dans handlers.py"""
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


def enregistrer_inline_handlers(bot):

    # =========================================================
    # Choix équipe 1 (bouton inline "home")
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("home|"))
    def choisir_home(call):
        user_id = call.from_user.id
        equipe = call.data.split("|", 1)[1]

        SESSIONS.setdefault(user_id, {})["home"] = equipe

        # Demander l'équipe 2
        langue = get_langue(user_id)
        bot.answer_callback_query(call.id, f"Equipe 1 : {equipe}")

        texte = "Equipe 1 selectionnee : " + equipe + "\n\nChoisis l'equipe 2 :"
        if langue == "en":
            texte = "Home team: " + equipe + "\n\nChoose away team:"
        elif langue == "ln":
            texte = "Ekip ya liboso: " + equipe + "\n\nPona ekip ya mibale:"

        bot.send_message(
            call.message.chat.id,
            texte,
            reply_markup=_clavier_lettres()
        )


    # =========================================================
    # Choix équipe 2 (bouton inline "away")
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("away|"))
    def choisir_away(call):
        user_id = call.from_user.id
        equipe = call.data.split("|", 1)[1]

        session = SESSIONS.get(user_id, {})
        home = session.get("home")

        if not home:
            bot.answer_callback_query(call.id, "Erreur de session. Recommence.")
            return

        # Vérifier la limite
        if not peut_faire_pronostic(user_id):
            langue = get_langue(user_id)
            bot.answer_callback_query(call.id, "Limite atteinte")
            bot.send_message(
                call.message.chat.id,
                get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
            )
            SESSIONS.pop(user_id, None)
            return

        # Générer le bulletin
        bot.answer_callback_query(call.id, "Analyse en cours...")

        try:
            resultat = predire_match(home, equipe)

            if "erreur" in resultat:
                bot.send_message(
                    call.message.chat.id,
                    f"Erreur : {resultat['erreur']}"
                )
                SESSIONS.pop(user_id, None)
                return

            langue = get_langue(user_id)
            bulletin = _formater_bulletin(resultat, langue)
            bot.send_message(call.message.chat.id, bulletin)

            sauvegarder_historique(
                resultat['home_team'], resultat['away_team'],
                resultat['p_h'], resultat['p_d'], resultat['p_a'],
                resultat['best_score'][0], resultat['best_score'][1]
            )

            incrementer_compteur(user_id)

        except Exception as e:
            print(f"Erreur prediction inline : {e}")
            bot.send_message(call.message.chat.id, f"Erreur : {str(e)}")

        SESSIONS.pop(user_id, None)


    # =========================================================
    # Lettres (A-Z)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("eq_letter|"))
    def choisir_lettre(call):
        user_id = call.from_user.id
        lettre = call.data.split("|")[1]

        equipes = _liste_equipes_par_lettre(lettre)

        if not equipes:
            bot.answer_callback_query(call.id, f"Aucune equipe avec '{lettre}'")
            return

        session = SESSIONS.get(user_id, {})
        prefixe = "away" if session.get("home") else "home"

        bot.answer_callback_query(call.id, f"{len(equipes)} equipe(s)")

        bot.send_message(
            call.message.chat.id,
            f"Equipes commencant par {lettre} :",
            reply_markup=_clavier_equipes(equipes, prefixe)
        )


    # =========================================================
    # Pagination
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("page|"))
    def paginer(call):
        parts = call.data.split("|")
        prefixe = parts[1]
        page = int(parts[2])

        # Récupérer la dernière lettre utilisée pour ce user
        # Pour simplifier, on affiche toutes les équipes filtrées par la 1ère lettre
        # Stockée en session
        user_id = call.from_user.id
        session = SESSIONS.get(user_id, {})
        lettre = session.get("lettre", None)

        equipes = _liste_equipes_par_lettre(lettre)

        if not equipes:
            bot.answer_callback_query(call.id, "Aucune equipe")
            return

        bot.answer_callback_query(call.id, f"Page {page + 1}")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=_clavier_equipes(equipes, prefixe, page=page)
        )


    # =========================================================
    # Annuler
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_prono")
    def annuler_prono(call):
        user_id = call.from_user.id
        SESSIONS.pop(user_id, None)
        bot.answer_callback_query(call.id, "Annule")
        bot.send_message(call.message.chat.id, "Selection annulee.")


    # =========================================================
    # Démarrer le mode inline
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == "start_inline_prono")
    def start_inline_prono(call):
        user_id = call.from_user.id

        if not peut_faire_pronostic(user_id):
            langue = get_langue(user_id)
            bot.answer_callback_query(call.id, "Limite atteinte")
            bot.send_message(
                call.message.chat.id,
                get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
            )
            return

        SESSIONS[user_id] = {}
        bot.answer_callback_query(call.id, "OK")

        bot.send_message(
            call.message.chat.id,
            "Choisis la 1ere lettre de l'equipe a domicile :",
            reply_markup=_clavier_lettres()
        )
