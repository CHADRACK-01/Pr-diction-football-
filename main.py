import threading
import telebot
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

from config import TOKEN, FICHIER_HISTORIQUE
from users import (
    initialiser_fichier_utilisateurs, enregistrer_utilisateur,
    get_statut_label, peut_faire_pronostic, get_compteur_jour,
    get_limite_jour, incrementer_compteur, set_premium
)
from model import (
    charger_et_entrainer, global_model_data,
    tache_arriere_plan_maj, predire_match, sauvegarder_historique
)


bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)


# =========================================================
# /start
# =========================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
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
        telebot.types.KeyboardButton("⭐ Passer Premium"),
    )

    welcome_text = (
        f"🤖 *Assistant Pro*\n\n"
        f"👤 Bienvenue *{user.first_name}* !\n"
        f"📊 Statut : *{statut_label}*\n"
        f"🎫 Pronostics aujourd'hui : *{compteur}/{limite}*\n\n"
        f"📈 Matchs en mémoire : *{nb_matchs}*\n"
        f"🎯 Précision IA : *{round(prec * 100, 2)}%*\n\n"
        "👇 *Utilisez les boutons ci-dessous :*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)


# =========================================================
# /update
# =========================================================
@bot.message_handler(commands=['update'])
def force_update_data(message):
    bot.reply_to(message, "⏳ Synchronisation en arrière-plan...")
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
    bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")


# =========================================================
# Menu principal
# =========================================================
@bot.message_handler(func=lambda m: True)
def handle_menu_clicks(message):
    text = message.text
    user_id = message.from_user.id

    if text == "📊 Statistiques du Modèle":
        prec = global_model_data.get('precision', 0.5)
        length = len(global_model_data.get('df', []))
        bot.reply_to(
            message,
            f"📊 Matchs analysés : {length}\n"
            f"🎯 Précision : {round(prec * 100, 2)}%"
        )

    elif text == "📜 Historique":
        try:
            import pandas as pd
            hist = pd.read_csv(FICHIER_HISTORIQUE)
            last_5 = hist.tail(5)
            texte = "📜 *Vos 5 derniers pronostics :*\n\n"
            for _, row in last_5.iterrows():
                texte += (
                    f"⚽ *{row['Match']}*\n"
                    f"📅 {row['Date_Consultation']}\n"
                    f"💡 {row['Pronostic_1N2']} | 🎯 {row['Score_Exact']}\n\n"
                )
            bot.reply_to(message, texte, parse_mode="Markdown")
        except FileNotFoundError:
            bot.reply_to(message, "⚠️ Aucun historique.")

    elif text == "⭐ Passer Premium":
        bot.reply_to(
            message,
            "⭐ *Abonnement Premium*\n\n"
            "💰 Tarif : 2000 FCFA / mois\n"
            "🎁 Avantages :\n"
            "  • Pronostics illimités\n"
            "  • Score exact + Over/BTTS\n"
            "  • Support prioritaire\n\n"
            "📲 Paiement : Mobile Money\n"
            "_Bientôt disponible..._",
            parse_mode="Markdown"
        )

    elif text == "⚽ Faire un Pronostic":
        if not peut_faire_pronostic(user_id):
            bot.reply_to(
                message,
                f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                "Passe en ⭐ *Premium* pour des pronostics illimités.",
                parse_mode="Markdown"
            )
            return
        bot.reply_to(message, "✍️ Tapez l'affiche :\n\n`EquipeDom vs EquipeExt`", parse_mode="Markdown")

    elif 'vs' in text.lower():
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
            bot.reply_to(message, f"❌ {resultat['erreur']}")
            return

        p_h, p_d, p_a = resultat['p_h'], resultat['p_d'], resultat['p_a']
        best_i, best_j = resultat['best_score']

        bulletin = (
            f"🏆 *{resultat['home_team']} vs {resultat['away_team']}*\n\n"
            f"📌 {resultat['fiabilite']}\n\n"
            f"📊 *1N2 :*\n"
            f"  • Domicile (1) : *{round(p_h*100,1)}%* (Cote: {round(1/p_h,2)})\n"
            f"  • Nul (N) : *{round(p_d*100,1)}%* (Cote: {round(1/p_d,2)})\n"
            f"  • Extérieur (2) : *{round(p_a*100,1)}%* (Cote: {round(1/p_a,2)})\n\n"
            f"⚽ *Buts :*\n"
            f"  • Plus de 2.5 buts : *{round(resultat['over_25']*100,1)}%*\n"
            f"  • BTTS : *{round(resultat['btts_yes']*100,1)}%*\n"
            f"  • 🎯 Score exact : *{best_i} - {best_j}*"
        )

        bot.reply_to(message, bulletin, parse_mode="Markdown")

        sauvegarder_historique(
            resultat['home_team'], resultat['away_team'],
            p_h, p_d, p_a, best_i, best_j
        )

        incrementer_compteur(user_id)

    else:
        bot.reply_to(message, "💡 Utilisez les boutons.")


# =========================================================
# WEBHOOK TELEGRAM (Render)
# =========================================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# =========================================================
# WEBHOOK PAWAPAY (confirmation de paiement)
# =========================================================
@app.route('/webhook/pawapay', methods=['POST'])
def webhook_pawapay():
    """Reçoit la confirmation de paiement de PawaPay."""
    try:
        data = request.get_json()
        print(f"🔔 Webhook PawaPay reçu : {data}")

        # PawaPay envoie le statut final ici
        if data.get("status") == "COMPLETED":
            deposit_id = data.get("depositId", "")
            # Format attendu : premium_<user_id>_<timestamp>
            parts = deposit_id.split("_")
            if len(parts) >= 2:
                user_id = int(parts[1])

                # Passer l'utilisateur en Premium pour 30 jours
                expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
                set_premium(user_id, expiration)

                # Notifier l'utilisateur sur Telegram
                bot.send_message(
                    user_id,
                    "🎉 *Paiement confirmé !*\n\n"
                    "Tu es maintenant ⭐ *Premium* pour 30 jours.\n"
                    "Profite de tes pronostics illimités 🚀",
                    parse_mode="Markdown"
                )

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"❌ Erreur webhook PawaPay : {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================================================
# ROUTE DE BASE
# =========================================================
@app.route('/')
def index():
    return "Bot opérationnel !", 200


# =========================================================
# LANCEMENT LOCAL
# =========================================================
if __name__ == "__main__":
    initialiser_fichier_utilisateurs()
    charger_et_entrainer()
    print("🚀 Bot lancé en mode polling local...")
    bot.infinity_polling()
