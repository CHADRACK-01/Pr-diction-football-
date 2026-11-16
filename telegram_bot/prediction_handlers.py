# telegram_bot/prediction_handlers.py
import telebot
from users import get_langue, est_premium
from core.feature_flags import est_active
from core.utils.logs import log_info, log_error, log_warning


def _traduire_pari(home, away, label_dc):
    """Traduit les codes 1X, X2, 12 en phrases positives."""
    if label_dc == "1X":
        return f"<b>{home}</b> va gagner ou faire match nul"
    elif label_dc == "X2":
        return f"<b>{away}</b> va gagner ou faire match nul"
    elif label_dc == "12":
        return "L'un des deux équipes va gagner (pas de match nul )"
    return label_dc


def _formater_bulletin_premium(resultat, langue="fr"):
    """Bulletin complet et visuel pour les utilisateurs Premium (HTML)."""
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

        txt = f"⚽ <b>{h} vs {a}</b>\n\n"
        txt += f"👋 Voici mon analyse pour ce match :\n"
        txt += f"J'ai regardé les statistiques et voici ce que je te conseille.\n\n"
        txt += f"👉 MON CONSEIL : {phrase_conseil}\n"
        txt += f"(J'ai <b>{round(proba_dc*100, 1)}%</b> de certitude).\n\n"

        txt += f"📊 <b>LES PROBABILITÉS :</b>\n"
        txt += f"• {h} gagne : {round(p_h*100, 1)}%\n"
        txt += f"• Match nul : {round(p_d*100, 1)}%\n"
        txt += f"• {a} gagne : {round(p_a*100, 1)}%\n\n"

        txt += f"🎯 <b>AUTRES OPTIONS :</b>\n"
        txt += f"• Les deux marquent : {'Oui' if btts > 0.5 else 'Non'} ({round(btts*100,1)}%)\n"
        txt += f"• Plus de 2.5 buts : {'Oui' if over > 0.5 else 'Non'} ({round(over*100,1)}%)\n\n"

        if top_scores:
            txt += f"🔮 <b>SCORES EXACTS PROBABLES :</b>\n"
            for i, (sh, sa, p) in enumerate(top_scores, 1):
                txt += f"{i}. {h} {sh} - {sa} {a} ({round(p, 1)}%)\n"
            txt += "\n"

        if h2h and h2h['total'] > 0:
            txt += f"📊 <b>HISTORIQUE (5 matchs) :</b>\n"
            txt += f"{h} a gagné {h2h['victoires_h']} fois, {h2h['nuls']} nul(s), {a} a gagné {h2h['victoires_a']} fois.\n\n"

        if analyse and analyse.get('cote_book'):
            txt += f"💰 <b>AVIS DU BOOKMAKER :</b>\n"
            txt += f"Cote proposée : {analyse['cote_book']}. "
            if analyse.get('is_value'):
                txt += f"🔥 <b>Value Bet Détecté !</b>\n\n"
            else:
                txt += f"Pas d'affaire exceptionnelle.\n\n"

        # --- Accès Pro aux Matrices de Poisson (Fonctionnalité 414) ---
        if est_active("414"):
            try:
                from core.nouveau_prediction import get_matrice_poisson
                matrice = get_matrice_poisson(h, a)
                if matrice:
                    txt += f"\n📐 <b>MATRICE DE POISSON (Top 5 Scores) :</b>\n"
                    for score in matrice["top_scores"][:5]:
                        txt += f"• {h} {score['score']} {a} : {score['proba']}%\n"
                    txt += f"\n📊 <b>Autres probabilités :</b>\n"
                    txt += f"• Plus de 2.5 buts : {matrice['proba_over_25']}%\n"
                    txt += f"• Les deux marquent : {matrice['proba_btts']}%\n"
                    txt += f"• Buts attendus (xG) : {matrice['lambda_home']} - {matrice['lambda_away']}\n\n"
            except Exception as e:
                log_warning(f"Impossible de générer la matrice de Poisson : {e}", "PREDICTION")

        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "💡 <i>Conseil du Coach : Ne mise jamais plus de 2% de ton argent total.</i>\n"
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin premium", "PREDICTION", exception=e)
        return "❌ Erreur."


def _formater_bulletin_free(resultat, langue="fr"):
    """Bulletin simplifié pour les utilisateurs Free (HTML)."""
    try:
        h = resultat.get('home_team', '?')
        a = resultat.get('away_team', '?')
        p_h, p_d, p_a = resultat.get('p_h', 0.33), resultat.get('p_d', 0.33), resultat.get('p_a', 0.33)
        
        dc_1x, dc_x2, dc_12 = resultat.get('dc_1x', 0.5), resultat.get('dc_x2', 0.5), resultat.get('dc_12', 0.5)
        label_dc, proba_dc = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])
        phrase_conseil = _traduire_pari(h, a, label_dc)

        txt = f"⚽ <b>{h} vs {a}</b>\n\n"
        txt += f"👋 Voici mon analyse :\n\n"
        txt += f"👉 MON CONSEIL : {phrase_conseil}\n"
        txt += f"(J'ai <b>{round(proba_dc*100, 1)}%</b> de certitude).\n\n"

        txt += f"📊 <b>PROBABILITÉS :</b>\n"
        txt += f"• {h} gagne : {round(p_h*100, 1)}%\n"
        txt += f"• Match nul : {round(p_d*100, 1)}%\n"
        txt += f"• {a} gagne : {round(p_a*100, 1)}%\n\n"

        txt += "━━━━━━━━━━━━━━━━━━━━\n"
        txt += "⭐ <i>Passe Premium pour voir les scores exacts et l'historique.</i>\n"
        return txt
    except Exception as e:
        log_error("Erreur formater bulletin free", "PREDICTION", exception=e)
        return "❌ Erreur."


def enregistrer_prediction_handlers(bot):
    log_info("Module prediction_handlers chargé.", "PREDICTION")
    
    @bot.message_handler(commands=['myid'])
    def cmd_myid(message):
        try:
            bot.reply_to(message, f"🆔 Ton ID : <code>{message.from_user.id}</code>", parse_mode="HTML")
        except Exception as e:
            log_error("Erreur ID", "PREDICTION", exception=e)
