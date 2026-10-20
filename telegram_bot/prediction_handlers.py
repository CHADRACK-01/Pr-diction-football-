import telebot

from users import (
    get_langue, est_banni, peut_faire_pronostic, get_limite_jour,
    incrementer_compteur, est_premium
)
from core.translations import get_text
from core.ml_model import global_model_data
from core.prediction import predire_match, sauvegarder_historique
from core.utils.logs import log_info
from core.session import get_session_competition, clear_session_competition


def _charger_modele():
    if global_model_data.get('df') is not None:
        return True
    log_info("Chargement des données de base depuis la BDD...", "PREDICTION")
    from core.ml_model import charger_et_entrainer
    charger_et_entrainer()
    return global_model_data.get('df') is not None


def _formater_bulletin_free(resultat, langue="fr"):
    h = resultat['home_team']
    a = resultat['away_team']
    p_h, p_d, p_a = resultat['p_h'], resultat['p_d'], resultat['p_a']
    dc_1x, dc_x2, dc_12 = resultat['dc_1x'], resultat['dc_x2'], resultat['dc_12']

    meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

    return (
        f"⚽ {h} vs {a}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 RÉSULTAT 1N2\n"
        f"• {h} : {round(p_h*100,1)}%\n"
        f"• Match nul : {round(p_d*100,1)}%\n"
        f"• {a} : {round(p_a*100,1)}%\n\n"
        f"🎯 DOUBLE CHANCE\n"
        f"• 1X : {round(dc_1x*100,1)}%\n"
        f"• X2 : {round(dc_x2*100,1)}%\n"
        f"• 12 : {round(dc_12*100,1)}%\n\n"
        f"💡 Recommandation : {meilleure_dc[0]} à {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Passe Premium pour voir les scores exacts, les tendances buts et les Value Bets !"
    )


def _formater_bulletin_premium(resultat, langue="fr"):
    h = resultat['home_team']
    a = resultat['away_team']
    p_h, p_d, p_a = resultat['p_h'], resultat['p_d'], resultat['p_a']
    dc_1x, dc_x2, dc_12 = resultat['dc_1x'], resultat['dc_x2'], resultat['dc_12']

    meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

    scores_txt = ""
    for i, (sh, sa, proba) in enumerate(resultat.get('top_scores', [])[:3], 1):
        scores_txt += f"{i}. {sh} - {sa} : {round(proba*100, 1)}%\n"

    analyse_txt = ""
    analyse = resultat.get('analyse_pari')
    if analyse:
        analyse_txt = (
            f"\n🔥 ANALYSE VALUE BET\n"
            f"• Reco : {analyse['label']} ({round(analyse['proba']*100, 1)}%)\n"
            f"• Cote Bot : {analyse['cote_bot']}\n"
        )
        if analyse['cote_book']:
            analyse_txt += f"• Cote Bookmaker : {analyse['cote_book']}\n"
            if analyse['is_value']:
                analyse_txt += f"✅ VALUE BET DÉTECTÉ !\n"

    return (
        f"⚽ {h} vs {a}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 RÉSULTAT 1N2\n"
        f"• {h} : {round(p_h*100,1)}% (Cote: {round(1/p_h, 2)})\n"
        f"• Match nul : {round(p_d*100,1)}% (Cote: {round(1/p_d, 2)})\n"
        f"• {a} : {round(p_a*100,1)}% (Cote: {round(1/p_a, 2)})\n\n"
        f"🎯 DOUBLE CHANCE\n"
        f"• 1X : {round(dc_1x*100,1)}%\n"
        f"• X2 : {round(dc_x2*100,1)}%\n"
        f"• 12 : {round(dc_12*100,1)}%\n\n"
        f"💡 Recommandation : {meilleure_dc[0]} à {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"⚽ TENDANCES BUTS\n"
        f"• Plus de 2.5 buts : {round(resultat['over_25']*100,1)}%\n"
        f"• Moins de 2.5 buts : {round(resultat['under_25']*100,1)}%\n"
        f"• Les 2 marquent (BTTS) : {round(resultat['btts_yes']*100,1)}%\n"
        f"• Pas les 2 : {round(resultat['btts_no']*100,1)}%\n\n"
        f"🏆 SCORES PROBABLES\n"
        f"{scores_txt}"
        f"{analyse_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Jouez de manière responsable."
    )


def enregistrer_prediction_handlers(bot):

    @bot.message_handler(func=lambda m: m.text and 'vs' in m.text.lower())
    def prediction_texte(message):
        print(f"[PREDICTION] Message reçu : {message.text}")
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        if not _charger_modele():
            bot.reply_to(message, "⚠️ Le modèle est en cours de chargement. Réessaie dans quelques instants.")
            return

        if not peut_faire_pronostic(user_id):
            bot.reply_to(message, get_text("limite_atteinte", langue, limite=get_limite_jour(user_id)))
            return

        parts = message.text.lower().split('vs')
        if len(parts) < 2:
            bot.reply_to(message, "Format invalide. Tape par exemple : PSG vs Marseille")
            return

        equipe_dom = parts[0].strip()
        equipe_ext = parts[1].strip()

        if not equipe_dom or not equipe_ext:
            bot.reply_to(message, "Format invalide. N'oublie pas les noms des deux équipes.")
            return

        # ⚠️ On récupère la compétition depuis la BDD
        competition = get_session_competition(user_id)
        
        print(f"[PREDICTION] Compétition pour {user_id} : '{competition}'")
        
        if competition == "default":
            bot.reply_to(message, "⚠️ Veuillez d'abord choisir une compétition en cliquant sur 'Faire un Pronostic'.")
            return

        resultat = predire_match(equipe_dom, equipe_ext, competition=competition)

        if "erreur" in resultat:
            bot.reply_to(message, resultat['erreur'])
            return

        # On supprime la session en BDD pour que le prochain pronostic redemande une compétition
        clear_session_competition(user_id)

        is_prem = est_premium(user_id)
        bulletin = _formater_bulletin_premium(resultat, langue) if is_prem else _formater_bulletin_free(resultat, langue)

        bot.reply_to(message, bulletin)

        sauvegarder_historique(
            resultat['home_team'], resultat['away_team'],
            resultat['p_h'], resultat['p_d'], resultat['p_a'],
            resultat['best_score'][0], resultat['best_score'][1]
        )
        incrementer_compteur(user_id)
