import threading
import io
import joblib
import telebot

from config import FICHIER_HISTORIQUE
from users import (
    enregistrer_utilisateur, get_statut_label, peut_faire_pronostic,
    get_compteur_jour, get_limite_jour, incrementer_compteur, est_premium,
    charger_modele_cache
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
    """Crée une barre de progression visuelle."""
    rempli = int(round(pct / 10))
    if rempli > 10:
        rempli = 10
    if rempli < 0:
        rempli = 0
    return "█" * rempli + "░" * (10 - rempli)


def _formater_bulletin(resultat):
    """Construit un bulletin propre et esthétique."""
    h = resultat['home_team']
    a = resultat['away_team']
    p_h = resultat['p_h']
    p_d = resultat['p_d']
    p_a = resultat['p_a']

    # Double Chance
    dc_1x = resultat['dc_1x']
    dc_x2 = resultat['dc_x2']
    dc_12 = resultat['dc_12']

    meilleure_dc = max(
        [("1X", dc_1x, "Domicile ou Nul"),
         ("X2", dc_x2, "Nul ou Extérieur"),
         ("12", dc_12, "Pas de match nul")],
        key=lambda x: x[1]
    )

    # Confiance globale
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

    # Top scores exacts
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
                f"╔══════════════════════════╗\n"
                f"║   📊 *STATISTIQUES IA*   ║\n"
                f"╚══════════════════════════╝\n\n"
                f"🧠 *Modèle entraîné*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📈 Matchs analysés : *{length}*\n"
                f"🎯 Précision : *{round(prec * 100, 2)}%*\n"
                f"⚙️ Algorithme : *RF + GB*\n"
                f"📊 Features : *30 variables*\n\n"
                f"_Modèle entraîné sur 5 ans de données_",
                parse_mode="Markdown"
            )

        # --- Historique ---
        elif text == "📜 Historique":
            try:
                import pandas as pd
                hist = pd.read_csv(FICHIER_HISTORIQUE)
                last_5 = hist.tail(5)
                texte = (
                    f"╔══════════════════════════╗\n"
                    f"║   📜 *HISTORIQUE*        ║\n"
                    f"╚══════════════════════════╝\n\n"
                    f"_Tes 5 derniers pronostics_\n\n"
                )
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

        # --- Passer Premium ---
        elif text == "⭐ Passer Premium":
            if est_premium(user_id):
                bot.reply_to(
                    message,
                    f"╔══════════════════════════╗\n"
                    f"║   ⭐ *PREMIUM ACTIF*     ║\n"
                    f"╚══════════════════════════╝\n\n"
                    f"✅ Tu es déjà *Premium* !\n\n"
                    f"🎁 Profite de tes pronostics illimités 🚀",
                    parse_mode="Markdown"
                )
                return
            bot.reply_to(
                message,
                f"╔══════════════════════════╗\n"
                f"║  ⭐ *ABONNEMENT PREMIUM* ║\n"
                f"╚══════════════════════════╝\n\n"
                f"🎁 *Avantages :*\n"
                f"  • ♾️ Pronostics illimités\n"
                f"  • 🎯 Score exact + Over/BTTS\n"
                f"  • 💬 Support prioritaire\n"
                f"  • 📊 Statistiques avancées\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💳 *Formules disponibles :*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 Journalier : *2 000 CDF*\n"
                f"📆 Hebdomadaire : *6 000 CDF*\n"
                f"🗓️ Mensuel : *10 000 CDF*\n\n"
                f"📲 _Paiement : Mobile Money_\n"
                f"_Bientôt disponible..._",
                parse_mode="Markdown"
            )

        # --- Faire un Pronostic ---
        elif text == "⚽ Faire un Pronostic":
            if not _charger_modele_si_necessaire(message, bot):
                return

            if not peut_faire_pronostic(user_id):
                bot.reply_to(
                    message,
                    f"╔══════════════════════════╗\n"
                    f"║   ⚠️ *LIMITE ATTEINTE*   ║\n"
                    f"╚══════════════════════════╝\n\n"
                    f"📊 Tu as utilisé tes *{get_limite_jour(user_id)}* pronostics du jour.\n\n"
                    f"⭐ Passe en *Premium* pour des pronostics illimités !",
                    parse_mode="Markdown"
                )
                return
            bot.reply_to(
                message,
                f"╔══════════════════════════╗\n"
                f"║  ✍️ *NOUVELLE AFFICHE*   ║\n"
                f"╚══════════════════════════╝\n\n"
                f"📝 Tape l'affiche du match :\n\n"
                f"`EquipeDom vs EquipeExt`\n\n"
                f"💡 *Exemples :*\n"
                f"  • `psg vs marseille`\n"
                f"  • `barca vs real`\n"
                f"  • `man city vs liverpool`",
                parse_mode="Markdown"
            )

        # --- Prédiction ---
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
                    f"💡 Vérifie l'orthographe des équipes.\n"
                    f"Essaye : `psg vs marseille`",
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

        # --- Fallback ---
        else:
            bot.reply_to(
                message,
                "💡 *Utilise les boutons du menu.*\n\n"
                "Ou tape : `Equipe A vs Equipe B`",
                parse_mode="Markdown"
            )
