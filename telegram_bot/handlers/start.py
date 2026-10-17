import io
import joblib
import telebot
import config

from users import (
    enregistrer_utilisateur, get_langue, set_langue, est_banni,
    get_user_info, est_administrateur, set_parrain, compter_filleuls,
    ajouter_jours_premium, get_palier_atteint, get_statut_label,
    get_compteur_jour, get_limite_jour
)
from core.translations import get_text, LANGUES_DISPONIBLES
from core.ml_model import global_model_data
from users import charger_modele_cache
from core.utils.logs import log_error

BOT_USERNAME = "MonPronosticFootball_bot"

def envoyer_menu_principal(chat_id, user_id, bot):
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

    welcome_text = get_text(
        "welcome", langue, nom=nom, statut=statut_label,
        compteur=compteur, limite=limite, nb_matchs=nb_matchs,
        precision=round(prec * 100, 2)
    )
    
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

    inline_markup = telebot.types.InlineKeyboardMarkup()
    inline_markup.add(
        telebot.types.InlineKeyboardButton("📢 Rejoindre notre Canal", url=config.CANAL_LIEN)
    )
    if est_administrateur(user_id):
        inline_markup.add(
            telebot.types.InlineKeyboardButton("🎛️ Ouvrir le Panneau Admin", callback_data="open_admin_panel")
        )
    bot.send_message(chat_id, "👇 Rejoins notre canal ou accède au panneau :", reply_markup=inline_markup)


def enregistrer_start_handlers(bot):

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        user = message.from_user
        if est_banni(user.id):
            bot.reply_to(message, get_text("banni", get_langue(user.id)))
            return

        existe_avant = get_user_info(user.id) is not None
        enregistrer_utilisateur(user.id, user.username, user.first_name)

        if not existe_avant and get_user_info(user.id) is not None:
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
                                bot.send_message(parrain_id, f"🎉 Nouveau filleul : {user.first_name}\n\n+1 jour Premium offert !\n📊 Total : {nb_filleuls} filleul(s){bonus_palier}")
                            except Exception: 
                                pass
                except Exception as e:
                    log_error(f"Erreur parrainage : {e}", "START")

        envoyer_menu_principal(message.chat.id, user.id, bot)

    @bot.message_handler(commands=['langue', 'language'])
    def cmd_langue(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for code, nom in LANGUES_DISPONIBLES.items():
            markup.add(telebot.types.InlineKeyboardButton(nom, callback_data=f"lang|{code}"))
        bot.reply_to(message, get_text("choix_langue", langue), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang|"))
    def traiter_langue(call):
        user_id = call.from_user.id
        langue = call.data.split("|")[1]
        if set_langue(user_id, langue):
            bot.answer_callback_query(call.id, "OK")
            bot.send_message(call.message.chat.id, get_text("langue_changee", langue))
            envoyer_menu_principal(call.message.chat.id, user_id, bot)
        else:
            bot.answer_callback_query(call.id, "Erreur")
