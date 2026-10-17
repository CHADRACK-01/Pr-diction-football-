import io
import joblib
import telebot

from users import (
    enregistrer_utilisateur,
    get_langue,
    set_langue,
    est_banni,
    get_user_info,
    est_administrateur,
    set_parrain,
    compter_filleuls,
    ajouter_jours_premium,
    get_palier_atteint
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.ml_model import global_model_data
from core.daily_matches import get_matchs_du_jour, formater_matchs_du_jour
from users import charger_modele_cache


# ⚠️ Remplace par le vrai nom de ton bot (sans @)
BOT_USERNAME = "MonPronosticFootball_bot"


def _charger_modele_si_necessaire(message, bot):
    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True

    try:
        cache = charger_modele_cache()
        if not cache:
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
        return True
    except Exception as e:
        print(f"Erreur chargement cache : {e}")
        return False


def envoyer_menu_principal(chat_id, user_id, bot):
    """Envoie le menu principal."""
    from users import (
        get_statut_label, get_compteur_jour, get_limite_jour
    )

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
        telebot.types.KeyboardButton(get_text("btn_coupons", langue)),
        telebot.types.KeyboardButton(get_text("btn_top_affiches", langue)),
        telebot.types.KeyboardButton(get_text("btn_historique", langue)),
        telebot.types.KeyboardButton(get_text("btn_stats", langue)),
        telebot.types.KeyboardButton(get_text("btn_notifs", langue)),
        telebot.types.KeyboardButton(get_text("btn_premium", langue)),
        telebot.types.KeyboardButton(get_text("btn_parrainage", langue)),
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


def enregistrer_menu_handlers(bot):

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user

        if est_banni(user.id):
            bot.reply_to(message, get_text("banni", get_langue(user.id)))
            return

        existe_avant = get_user_info(user.id) is not None

        enregistrer_utilisateur(user.id, user.username, user.first_name)

        # Détection du parrain
        if not existe_avant:
            parts = message.text.split()
            if len(parts) >= 2 and parts[1].startswith("REF"):
                try:
                    parrain_id = int(parts[1].replace("REF", ""))
                    if parrain_id != user.id and get_user_info(parrain_id):
                        if set_parrain(user.id, parrain_id):
                            ajouter_jours_premium(user.id, 1)
                            ajouter_jours_premium(parrain_id, 1)

                            langue = get_langue(user.id)

                            try:
                                bot.send_message(user.id, get_text("parrainage_bienvenue", langue))
                            except Exception:
                                pass

                            nb_filleuls = compter_filleuls(parrain_id)

                            palier = get_palier_atteint(nb_filleuls)
                            bonus_palier = ""
                            if palier and nb_filleuls in [5, 10, 20, 50]:
                                ajouter_jours_premium(parrain_id, palier['bonus'])
                                bonus_palier = f"\n\n🏆 Palier {palier['nom']} atteint ! +{palier['bonus']} jours bonus"

                            try:
                                bot.send_message(
                                    parrain_id,
                                    f"🎉 Nouveau filleul : {user.first_name}\n\n"
                                    f"+1 jour Premium offert !\n"
                                    f"📊 Total : {nb_filleuls} filleul(s){bonus_palier}"
                                )
                            except Exception:
                                pass

                except Exception as e:
                    print(f"⚠️ Erreur parrainage : {e}")

        envoyer_menu_principal(message.chat.id, user.id, bot)


    # Fallback
    @bot.message_handler(func=lambda message: True)
    def handle_menu_fallback(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        pass
