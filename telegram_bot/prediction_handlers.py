import telebot

from users import (
    get_langue, est_banni, peut_faire_pronostic, get_limite_jour,
    incrementer_compteur, est_premium
)
from core.translations import get_text
from core.ml_model import global_model_data
from core.prediction import predire_match, sauvegarder_historique
from core.utils.logs import log_info, log_error, log_warning
from core.session import get_session_competition, clear_session_competition
from config import MAPPING_COMPETITIONS


def _charger_modele():
    """Charge les modèles si nécessaire (log en cas d'échec)."""
    if global_model_data.get('modeles_par_competition') is not None:
        return True
    log_info("Chargement des modèles depuis la BDD...", "PREDICTION")
    from core.ml_model import charger_et_entrainer
    return charger_et_entrainer()


def _formater_bulletin_free(resultat, langue="fr"):
    """Bulletin pour les utilisateurs Free (3 marchés principaux)."""
    h = resultat['home_team']
    a = resultat['away_team']
    
    dc_1x = resultat.get('dc_1x', 0.5)
    dc_x2 = resultat.get('dc_x2', 0.5)
    dc_12 = resultat.get('dc_12', 0.5)
    meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

    btts = resultat.get('btts_yes', 0.5)
    over = resultat.get('over_25', 0.5)

    return (
        f"⚽ **{h} vs {a}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ **DOUBLE CHANCE**\n"
        f"• 1X : {round(dc_1x*100,1)}%\n"
        f"• X2 : {round(dc_x2*100,1)}%\n"
        f"• 12 : {round(dc_12*100,1)}%\n"
        f"👉 **Reco : {meilleure_dc[0]}** à {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"🎯 **BTTS (Les 2 marquent)**\n"
        f"• Oui : {round(btts*100,1)}%\n"
        f"• Non : {round((1-btts)*100,1)}%\n\n"
        f"🥅 **TOTAL BUTS (Over 2.5)**\n"
        f"• Plus de 2.5 : {round(over*100,1)}%\n"
        f"• Moins de 2.5 : {round((1-over)*100,1)}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ _Passe Premium pour voir les marchés Mi-temps, les scores exacts et les Value Bets !_"
    )


def _formater_bulletin_premium(resultat, langue="fr"):
    """Bulletin complet pour les utilisateurs Premium (5 marchés + Value Bet)."""
    h = resultat['home_team']
    a = resultat['away_team']
    
    dc_1x = resultat.get('dc_1x', 0.5)
    dc_x2 = resultat.get('dc_x2', 0.5)
    dc_12 = resultat.get('dc_12', 0.5)
    meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

    btts = resultat.get('btts_yes', 0.5)
    over = resultat.get('over_25', 0.5)
    
    ht_prolific = resultat.get('ht_prolific', {})
    htr = resultat.get('htr', {})
    
    analyse_txt = ""
    analyse = resultat.get('analyse_pari')
    if analyse:
        analyse_txt = (
            f"\n🔥 **ANALYSE VALUE BET**\n"
            f"• Reco : {analyse['label']} ({round(analyse['proba']*100, 1)}%)\n"
            f"• Cote Bot : {analyse['cote_bot']}\n"
        )
        if analyse.get('cote_book'):
            analyse_txt += f"• Cote Bookmaker : {analyse['cote_book']}\n"
            if analyse.get('is_value'):
                analyse_txt += f"✅ **VALUE BET DÉTECTÉ !**\n"

    return (
        f"⚽ **{h} vs {a}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ **DOUBLE CHANCE**\n"
        f"• 1X : {round(dc_1x*100,1)}%\n"
        f"• X2 : {round(dc_x2*100,1)}%\n"
        f"• 12 : {round(dc_12*100,1)}%\n"
        f"👉 **Reco : {meilleure_dc[0]}** à {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"🎯 **BTTS (Les 2 marquent)**\n"
        f"• Oui : {round(btts*100,1)}% | Non : {round((1-btts)*100,1)}%\n\n"
        f"🥅 **TOTAL BUTS (Over 2.5)**\n"
        f"• Plus de 2.5 : {round(over*100,1)}% | Moins : {round((1-over)*100,1)}%\n\n"
        f"⏱️ **MI-TEMPS LA PLUS PROLIFIQUE**\n"
        f"• 1ère MT : {round(ht_prolific.get('1ere_mt', 0.33)*100,1)}%\n"
        f"• 2ème MT : {round(ht_prolific.get('2eme_mt', 0.33)*100,1)}%\n"
        f"• Égalité : {round(ht_prolific.get('egalite', 0.33)*100,1)}%\n\n"
        f"🏁 **1N2 À LA MI-TEMPS**\n"
        f"• 1 : {round(htr.get('1', 0.33)*100,1)}% | N : {round(htr.get('N', 0.33)*100,1)}% | 2 : {round(htr.get('2', 0.33)*100,1)}%\n"
        f"{analyse_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ _Les marchés Mi-temps sont indicatifs._\n"
        f"Jouez de manière responsable."
    )


def enregistrer_prediction_handlers(bot):

    @bot.message_handler(func=lambda m: m.text and ' vs ' in m.text.lower())
    def prediction_texte(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        
        log_info(f"Demande de prédiction de {user_id} : '{message.text}'", "PREDICTION")

        # 1. Vérification banni
        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", langue))
                return
        except Exception as e:
            log_error(f"Impossible de vérifier si {user_id} est banni", "PREDICTION", exception=e)
            return

        # 2. Chargement des modèles
        if not _charger_modele():
            bot.reply_to(message, "⚠️ Le modèle est en cours de chargement ou indisponible. Réessaie dans quelques instants.")
            return

        # 3. Vérification de la limite
        try:
            if not peut_faire_pronostic(user_id):
                limite = get_limite_jour(user_id)
                bot.reply_to(message, get_text("limite_atteinte", langue, limite=limite))
                return
        except Exception as e:
            log_error(f"Impossible de vérifier la limite de {user_id}", "PREDICTION", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la vérification de tes limites. Réessaie.")
            return

        # 4. Parsing du match
        parts = message.text.lower().split(' vs ')
        if len(parts) != 2:
            bot.reply_to(message, "Format invalide. Tape par exemple : Paris SG vs Marseille")
            return

        equipe_dom = parts[0].strip()
        equipe_ext = parts[1].strip()

        if not equipe_dom or not equipe_ext:
            bot.reply_to(message, "Format invalide. N'oublie pas les noms des deux équipes.")
            return

        # 5. Récupération de la compétition
        try:
            competition_code = get_session_competition(user_id)
        except Exception as e:
            log_error(f"Impossible de récupérer la compétition de {user_id}", "PREDICTION", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la récupération de ta compétition. Réessaie.")
            return
        
        if competition_code == "default":
            bot.reply_to(message, "⚠️ Veuillez d'abord choisir une compétition en cliquant sur '⚽ Faire un Pronostic'.")
            return
        
        # Conversion : code (ligue_1) -> nom (Ligue 1)
        competition_reelle = MAPPING_COMPETITIONS.get(competition_code, competition_code)

        # 6. Prédiction (gère ses propres erreurs en interne)
        resultat = predire_match(equipe_dom, equipe_ext, competition=competition_reelle)

        if "erreur" in resultat:
            erreur_msg = resultat["erreur"]
            # Les erreurs "utilisateur" (équipe non trouvée) ne sont pas anormales
            if "Données insuffisantes" in erreur_msg or "non supportée" in erreur_msg:
                bot.reply_to(message, erreur_msg)
            else:
                # Erreur système : on logge
                log_error(f"Erreur de prédiction pour {equipe_dom} vs {equipe_ext} : {erreur_msg}", "PREDICTION")
                bot.reply_to(message, f"❌ {erreur_msg}")
            return

        # 7. Suppression de la session (non bloquant)
        try:
            clear_session_competition(user_id)
        except Exception as e:
            log_warning(f"Impossible de supprimer la session de {user_id} : {e}", "PREDICTION")

        # 8. Affichage du bulletin
        try:
            is_prem = est_premium(user_id)
            bulletin = _formater_bulletin_premium(resultat, langue) if is_prem else _formater_bulletin_free(resultat, langue)
            bot.reply_to(message, bulletin, parse_mode='Markdown')
        except Exception as e:
            log_error(f"Impossible d'afficher le bulletin pour {user_id}", "PREDICTION", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'affichage du bulletin.")
            return

        # 9. Sauvegarde de l'historique
        try:
            sauvegarder_historique(
                resultat['home_team'], resultat['away_team'],
                resultat['p_h'], resultat['p_d'], resultat['p_a'],
                resultat['best_score'][0], resultat['best_score'][1]
            )
        except Exception as e:
            log_error(f"Impossible de sauvegarder l'historique pour {user_id}", "PREDICTION", exception=e)

        # 10. Incrémentation du compteur
        try:
            incrementer_compteur(user_id)
        except Exception as e:
            log_error(f"Impossible d'incrémenter le compteur de {user_id}", "PREDICTION", exception=e)
