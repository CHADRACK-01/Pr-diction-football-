# telegram_bot/prediction_handlers.py
import telebot
from users import get_langue, est_premium
from core.utils.logs import log_info, log_error, log_warning

def _formater_bulletin_free(resultat, langue="fr"):
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
        txt += f"📊 **PROBABILITÉS (1N2) :**\n"
        txt += f"• Victoire {h} : {round(p_h*100, 1)}%\n"
        txt += f"• Match Nul : {round(p_d*100, 1)}%\n"
        txt += f"• Victoire {a} : {round(p_a*100, 1)}%\n\n"
        txt += f"🏆 **CONSEIL DU JOUR :**\n"
        txt += f"👉 **Double Chance {meilleure_dc[0]}** ({round(meilleure_dc[1]*100, 1)}%)\n\n"
        txt += f"🎯 **STATISTIQUES :**\n"
        txt += f"• BTTS : {round(btts*100,1)}% | Over 2.5 : {round(over*100,1)}%\n\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "⭐ _Passe Premium pour voir les scores exacts et le H2H._\n"
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin free", "PREDICTION", exception=e)
        return "❌ Erreur."

def _formater_bulletin_premium(resultat, langue="fr"):
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
        top_scores = resultat.get('top_scores', [])
        h2h = resultat.get('h2h')
        analyse = resultat.get('analyse_pari')

        txt = f"⚽ **{h}** 🆚 **{a}**\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n\n"
        txt += f"📊 **PROBABILITÉS (1N2) :**\n"
        txt += f"• Victoire {h} : {round(p_h*100, 1)}%\n"
        txt += f"• Match Nul : {round(p_d*100, 1)}%\n"
        txt += f"• Victoire {a} : {round(p_a*100, 1)}%\n\n"
        txt += f"🏆 **PRONOSTIC CONSEILLÉ :**\n"
        txt += f"👉 **Double Chance {meilleure_dc[0]}** ({round(meilleure_dc[1]*100, 1)}%)\n\n"
        txt += f"🎯 **AUTRES MARCHÉS :**\n"
        txt += f"• BTTS : **{'Oui' if btts > 0.5 else 'Non'}** ({round(btts*100,1)}%)\n"
        txt += f"• Over 2.5 : **{'Oui' if over > 0.5 else 'Non'}** ({round(over*100,1)}%)\n\n"
        if top_scores:
            txt += f"🔮 **SCORES EXACTS :**\n"
            for i, (sh, sa, p) in enumerate(top_scores, 1):
                txt += f"{i}. {h} {sh}-{sa} {a} ({round(p, 1)}%)\n"
            txt += "\n"
        if h2h and h2h['total'] > 0:
            txt += f"📊 **H2H (5 derniers) :**\n"
            txt += f"• {h} : {h2h['victoires_h']} | Nuls : {h2h['nuls']} | {a} : {h2h['victoires_a']}\n\n"
        if analyse and analyse.get('cote_book'):
            txt += f"💰 **VALUE BET :**\n"
            txt += f"• Cote Book : {analyse['cote_book']} | Cote IA : {analyse['cote_bot']}\n"
            if analyse.get('is_value'):
                txt += f"🔥 **VALUE BET DÉTECTÉ !**\n"
            txt += "\n"
        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "💡 _Misez max 2% de votre capital._\n"
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin premium", "PREDICTION", exception=e)
        return "❌ Erreur."

def enregistrer_prediction_handlers(bot):
    log_info("Module prediction_handlers chargé.", "PREDICTION")
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        try:
            bot.reply_to(message, f"🆔 Ton ID : `{message.from_user.id}`", parse_mode="Markdown")
        except Exception as e:
            log_error("Erreur ID", "PREDICTION", exception=e)
