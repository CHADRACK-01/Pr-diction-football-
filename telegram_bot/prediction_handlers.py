# telegram_bot/prediction_handlers.py
import telebot
from users import get_langue, est_premium
from core.utils.logs import log_info, log_error, log_warning


def _formater_bulletin_free(resultat, langue="fr"):
    """Bulletin simplifié pour les utilisateurs Free (avec 1N2)."""
    try:
        h = resultat.get('home_team', '?')
        a = resultat.get('away_team', '?')
        
        p_h = resultat.get('p_h', 0.33)
        p_d = resultat.get('p_d', 0.33)
        p_a = resultat.get('p_a', 0.33)

        dc_1x = resultat.get('dc_1x', 0.5)
        dc_x2 = resultat.get('dc_x2', 0.5)
        dc_12 = resultat.get('dc_12', 0.5)
        meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])
        
        btts = resultat.get('btts_yes', 0.5)
        over = resultat.get('over_25', 0.5)

        txt = f"⚽ **{h}** 🆚 **{a}**\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # 1N2 (Version Free)
        txt += f"📊 **PROBABILITÉS (1N2) :**\n"
        txt += f"• Victoire {h} : {round(p_h*100, 1)}%\n"
        txt += f"• Match Nul : {round(p_d*100, 1)}%\n"
        txt += f"• Victoire {a} : {round(p_a*100, 1)}%\n\n"
        
        txt += f"🏆 **CONSEIL DU JOUR :**\n"
        txt += f"👉 **Double Chance {meilleure_dc[0]}** ({round(meilleure_dc[1]*100, 1)}%)\n\n"

        txt += f"🎯 **STATISTIQUES :**\n"
        txt += f"• BTTS : {round(btts*100,1)}% | Over 2.5 : {round(over*100,1)}%\n\n"

        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "⭐ _Passe Premium pour voir :_\n"
        txt += "• Les scores exacts\n"
        txt += "• L'historique des confrontations\n"
        txt += "• L'analyse des cotes (Value Bet)\n"
        
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin free", "PREDICTION", exception=e)
        return "❌ Erreur lors de la génération du bulletin."


def _formater_bulletin_premium(resultat, langue="fr"):
    """Bulletin complet et visuel pour les utilisateurs Premium (avec 1N2)."""
    try:
        h = resultat.get('home_team', '?')
        a = resultat.get('away_team', '?')
        
        # 1N2
        p_h = resultat.get('p_h', 0.33)
        p_d = resultat.get('p_d', 0.33)
        p_a = resultat.get('p_a', 0.33)

        # Double Chance
        dc_1x = resultat.get('dc_1x', 0.5)
        dc_x2 = resultat.get('dc_x2', 0.5)
        dc_12 = resultat.get('dc_12', 0.5)
        meilleure_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

        btts = resultat.get('btts_yes', 0.5)
        over = resultat.get('over_25', 0.5)
        top_scores = resultat.get('top_scores', [])
        h2h = resultat.get('h2h')
        analyse = resultat.get('analyse_pari')

        txt = f"⚽ **{h}** 🆚 **{a}**\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # 1N2 (Version Premium)
        txt += f"📊 **PROBABILITÉS (1N2) :**\n"
        txt += f"• Victoire {h} : {round(p_h*100, 1)}%\n"
        txt += f"• Match Nul : {round(p_d*100, 1)}%\n"
        txt += f"• Victoire {a} : {round(p_a*100, 1)}%\n\n"

        # Conseil principal
        txt += f"🏆 **PRONOSTIC CONSEILLÉ :**\n"
        txt += f"👉 **Double Chance {meilleure_dc[0]}** ({round(meilleure_dc[1]*100, 1)}% de chances)\n\n"

        # Marchés secondaires
        txt += f"🎯 **AUTRES MARCHÉS :**\n"
        txt += f"• Les 2 marquent : **{'Oui' if btts > 0.5 else 'Non'}** ({round(btts*100,1)}%)\n"
        txt += f"• Plus de 2.5 buts : **{'Oui' if over > 0.5 else 'Non'}** ({round(over*100,1)}%)\n\n"

        # Scores exacts
        if top_scores:
            txt += f"🔮 **SCORES EXACTS PROBABLES :**\n"
            for i, (sh, sa, p) in enumerate(top_scores, 1):
                txt += f"{i}. **{h} {sh} - {sa} {a}** ({round(p, 1)}%)\n"
            txt += "\n"

        # H2H
        if h2h and h2h['total'] > 0:
            txt += f"📊 **HISTORIQUE (5 derniers matchs) :**\n"
            txt += f"• Victoires {h} : {h2h['victoires_h']}\n"
            txt += f"• Matchs nuls : {h2h['nuls']}\n"
            txt += f"• Victoires {a} : {h2h['victoires_a']}\n\n"

        # Value Bet
        if analyse and analyse.get('cote_book'):
            txt += f"💰 **ANALYSE VALUE BET :**\n"
            txt += f"• Cote Bookmaker : {analyse['cote_book']}\n"
            txt += f"• Cote Juste (IA) : {analyse['cote_bot']}\n"
            if analyse.get('is_value'):
                txt += f"🔥 **VALUE BET DÉTECTÉ !** (Le bookmaker sous-évalue cette cote)\n"
            else:
                txt += f"⚖️ Pas de valeur détectée (Cote trop basse)\n"
            txt += "\n"

        # Conseil Bankroll
        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "💡 **CONSEIL DE MISE :**\n"
        txt += "_Ne misez jamais plus de 2% de votre capital total sur un seul pari._\n"
        
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin premium", "PREDICTION", exception=e)
        return "❌ Erreur lors de la génération du bulletin."


def enregistrer_prediction_handlers(bot):
    """Module de formatage uniquement, pas de handler de saisie."""
    log_info("Module prediction_handlers chargé.", "PREDICTION")
    
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        try:
            user_id = message.from_user.id
            bot.reply_to(message, f"🆔 Ton ID : `{user_id}`", parse_mode="Markdown")
        except Exception as e:
            log_error("Impossible d'afficher l'ID", "PREDICTION", exception=e)
