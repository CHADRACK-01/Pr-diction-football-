# telegram_bot/prediction_handlers.py
import telebot
from users import get_langue, est_premium
from core.utils.logs import log_info, log_error, log_warning

def _traduire_pari(home, away, label_dc):
    """Traduit 1X, X2, 12 en phrase compréhensible."""
    if label_dc == "1X":
        return f"**{home}** gagne ou fait match nul"
    elif label_dc == "X2":
        return f"**{away}** gagne ou fait match nul"
    elif label_dc == "12":
        return "Il n'y aura **pas de match nul**"
    return label_dc

def _formater_bulletin_premium(resultat, langue="fr"):
    try:
        h = resultat.get('home_team', '?')
        a = resultat.get('away_team', '?')
        p_h, p_d, p_a = resultat.get('p_h', 0.33), resultat.get('p_d', 0.33), resultat.get('p_a', 0.33)
        
        dc_1x, dc_x2, dc_12 = resultat.get('dc_1x', 0.5), resultat.get('dc_x2', 0.5), resultat.get('dc_12', 0.5)
        label_dc, proba_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])
        phrase_conseil = _traduire_pari(h, a, label_dc)

        btts = resultat.get('btts_yes', 0.5)
        over = resultat.get('over_25', 0.5)
        top_scores = resultat.get('top_scores', [])
        h2h = resultat.get('h2h')
        analyse = resultat.get('analyse_pari')

        txt = f"⚽ **{h} vs {a}**\n\n"
        txt += f"👋 Voici mon analyse pour ce match :\n"
        txt += f"J'ai regardé les statistiques et voici ce que je te conseille.\n\n"
        txt += f"👉 **Mon conseil : \"{phrase_conseil}\"**\n"
        txt += f"(J'ai {round(proba_dc*100, 1)}% de certitude que ce pari soit gagnant).\n\n"

        txt += f"📊 **Les probabilités du match :**\n"
        txt += f"• {h} gagne : {round(p_h*100, 1)}%\n"
        txt += f"• Match nul : {round(p_d*100, 1)}%\n"
        txt += f"• {a} gagne : {round(p_a*100, 1)}%\n\n"

        txt += f"🎯 **Autres options intéressantes :**\n"
        txt += f"• Les deux équipes marquent : {'Oui' if btts > 0.5 else 'Non'} ({round(btts*100,1)}%)\n"
        txt += f"• Plus de 2.5 buts : {'Oui' if over > 0.5 else 'Non'} ({round(over*100,1)}%)\n\n"

        if top_scores:
            txt += f"🔮 **Les scores exacts les plus probables :**\n"
            for i, (sh, sa, p) in enumerate(top_scores, 1):
                txt += f"{i}. {h} {sh} - {sa} {a} ({round(p, 1)}%)\n"
            txt += "\n"

        if h2h and h2h['total'] > 0:
            txt += f"📊 **Historique des 5 derniers matchs :**\n"
            txt += f"{h} a gagné {h2h['victoires_h']} fois, {h2h['nuls']} match(s) nul(s), {a} a gagné {h2h['victoires_a']} fois.\n\n"

        if analyse and analyse.get('cote_book'):
            txt += f"💰 **L'avis du bookmaker :**\n"
            txt += f"Il propose une cote de {analyse['cote_book']}. "
            if analyse.get('is_value'):
                txt += f"🔥 **C'est une très bonne affaire (Value Bet) !**\n\n"
            else:
                txt += f"Ce n'est pas une affaire exceptionnelle.\n\n"

        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "💡 **Conseil du Coach :** Ne mise jamais plus de 2% de ton argent total sur un seul pari.\n"
        
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin premium", "PREDICTION", exception=e)
        return "❌ Erreur lors de la génération du bulletin."

def _formater_bulletin_free(resultat, langue="fr"):
    try:
        h = resultat.get('home_team', '?')
        a = resultat.get('away_team', '?')
        p_h, p_d, p_a = resultat.get('p_h', 0.33), resultat.get('p_d', 0.33), resultat.get('p_a', 0.33)
        
        dc_1x, dc_x2, dc_12 = resultat.get('dc_1x', 0.5), resultat.get('dc_x2', 0.5), resultat.get('dc_12', 0.5)
        label_dc, proba_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])
        phrase_conseil = _traduire_pari(h, a, label_dc)

        txt = f"⚽ **{h} vs {a}**\n\n"
        txt += f"👋 Voici mon analyse pour ce match :\n\n"
        txt += f"👉 **Mon conseil : \"{phrase_conseil}\"**\n"
        txt += f"(J'ai {round(proba_dc*100, 1)}% de certitude).\n\n"

        txt += f"📊 **Les probabilités du match :**\n"
        txt += f"• {h} gagne : {round(p_h*100, 1)}%\n"
        txt += f"• Match nul : {round(p_d*100, 1)}%\n"
        txt += f"• {a} gagne : {round(p_a*100, 1)}%\n\n"

        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "⭐ _Passe Premium pour voir les scores exacts et l'historique des matchs._\n"
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin free", "PREDICTION", exception=e)
        return "❌ Erreur."

def enregistrer_prediction_handlers(bot):
    log_info("Module prediction_handlers chargé.", "PREDICTION")
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        try:
            bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")
        except Exception as e:
            log_error("Erreur ID", "PREDICTION", exception=e)
