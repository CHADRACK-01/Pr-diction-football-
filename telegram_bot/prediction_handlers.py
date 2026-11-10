import telebot

from users import get_langue, est_premium
from core.utils.logs import log_info, log_error, log_warning


def _formater_bulletin_free(resultat, langue="fr"):
    """
    Bulletin pour les utilisateurs Free (3 marchés principaux : DC, BTTS, Over).
    """
    try:
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
            f"⭐ _Passe Premium pour voir les marchés Mi-temps et les Value Bets !_"
        )
    except Exception as e:
        log_error("Impossible de formater le bulletin Free", "PREDICTION", exception=e)
        return "❌ Erreur lors de la génération du bulletin."


def _formater_bulletin_premium(resultat, langue="fr"):
    """
    Bulletin complet pour les utilisateurs Premium (5 marchés + Value Bet).
    """
    try:
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
    except Exception as e:
        log_error("Impossible de formater le bulletin Premium", "PREDICTION", exception=e)
        return "❌ Erreur lors de la génération du bulletin."


def enregistrer_prediction_handlers(bot):
    """
    ⚠️ Ce module n'enregistre plus de handler de saisie libre.
    La prédiction se fait maintenant via le clavier dynamique dans pronostic.py.
    Les fonctions _formater_bulletin_free et _formater_bulletin_premium 
    sont importées par pronostic.py.
    """
    log_info("Module prediction_handlers chargé (formatage uniquement, pas de handler).", "PREDICTION")
    
    # On garde un handler pour /myid (utilitaire)
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        """Affiche l'ID de l'utilisateur (utile pour l'admin)."""
        try:
            user_id = message.from_user.id
            bot.reply_to(message, f"🆔 Ton ID : `{user_id}`", parse_mode="Markdown")
        except Exception as e:
            log_error("Impossible d'afficher l'ID utilisateur", "PREDICTION", exception=e)
