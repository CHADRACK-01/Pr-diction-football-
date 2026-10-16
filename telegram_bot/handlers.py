import threading
import telebot

from config import FICHIER_HISTORIQUE
from users import (
    enregistrer_utilisateur, get_statut_label, peut_faire_pronostic,
    get_compteur_jour, get_limite_jour, incrementer_compteur, est_premium
)
from core.ml_model import (
    charger_et_entrainer, global_model_data, tache_arriere_plan_maj
)
from core.prediction import predire_match, sauvegarder_historique


def _charger_modele_si_necessaire(message, bot):
    """Lazy loading : charge le modèle si pas encore en mémoire."""
    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True

    bot.reply_to(message, "⏳ Premier lancement : chargement du modèle (1-2 min)...")
    try:
        charger_et_entrainer()
        if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
            return True
        else:
            bot.reply_to(
                message,
                "⚠️ Aucun match en base.\n\n"
                "Envoie /update pour télécharger les données (cela prend 1-2 min)."
            )
            return False
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur chargement : {e}")
        return False


def enregistrer_handlers(bot):

    # =========================================================
    # /start et /help
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
        bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")


    # =========================================================
    # Menu principal
    # =========================================================
    @bot.message_handler(func=lambda message: True)
    def handle_menu_clicks(message):
        text = message.text
        user_id = message.from_user.id

        # --- Statistiques du Modèle ---
        if text == "📊 Statistiques du Modèle":
            prec = global_model_data.get('precision', 0.5)
            length = len(global_model_data.get('df', []))
            bot.reply_to(
                message,
                f"📊 Matchs analysés : {length}\n"
                f"🎯 Précision : {round(prec * 100, 2)}%"
            )

        # --- Historique ---
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

        # --- Passer Premium ---
        elif text == "⭐ Passer Premium":
            if est_premium(user_id):
                bot.reply_to(
                    message,
                    "✅ *Tu es déjà Premium !*\n\nProfite bien de tes pronostics illimités 🚀",
                    parse_mode="Markdown"
                )
                return
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

        # --- Faire un Pronostic ---
        elif text == "⚽ Faire un Pronostic":
            # Lazy loading
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"⚠️ *Limite atteinte* ({get_limite_jour(user_id)}/jour).\n\n"
                    "Passe en ⭐ *Premium* pour des pronostics illimités.",
                    parse_mode="Markdown"
                )
                return
            bot.reply_to(message, "✍️ Tapez l'affiche :\n\n`EquipeDom vs EquipeExt`", parse_mode="Markdown")

        # --- Prédiction ---
        elif 'vs' in text.lower():
            # Lazy loading
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

        # --- Fallback ---
        else:
            bot.reply_to(message, "💡 Utilisez les boutons.")
