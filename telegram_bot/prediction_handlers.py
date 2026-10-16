import io
import joblib
import telebot

from users import (
    get_langue, est_banni, peut_faire_pronostic, get_limite_jour,
    incrementer_compteur
)
from core.translations import get_text
from core.ml_model import global_model_data, charger_modele_cache
from core.prediction import predire_match, sauvegarder_historique


def _charger_modele():
    if global_model_data.get('df') is not None and len(global_model_data.get('df', [])) > 0:
        return True
    try:
        cache = charger_modele_cache()
        if not cache:
            return False
        modele_bytes, precision, nb_matchs = cache
        buffer = io.BytesIO(modele_bytes)
        donnees = joblib.load(buffer)
        global_model_data.update(donnees)
        global_model_data['precision'] = precision
        return True
    except Exception as e:
        print(f"Erreur chargement cache : {e}")
        return False


def _formater_bulletin(resultat, langue="fr"):
    h = resultat['home_team']
    a = resultat['away_team']
    p_h, p_d, p_a = resultat['p_h'], resultat['p_d'], resultat['p_a']
    dc_1x, dc_x2, dc_12 = resultat['dc_1x'], resultat['dc_x2'], resultat['dc_12']

    meilleure_dc = max(
        [("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)],
        key=lambda x: x[1]
    )

    scores_txt = ""
    for i, (sh, sa, proba) in enumerate(resultat.get('top_scores', [])[:3], 1):
        scores_txt += f"{i}. {sh} - {sa} : {round(proba*100, 1)}%\n"

    return (
        f"PRONOSTIC FOOTBALL\n"
        f"========================\n\n"
        f"{h} vs {a}\n\n"
        f"RESULTAT 1N2\n"
        f"------------------------\n"
        f"{h} : {round(p_h*100,1)}% ({round(1/p_h, 2)})\n"
        f"Match nul : {round(p_d*100,1)}% ({round(1/p_d, 2)})\n"
        f"{a} : {round(p_a*100,1)}% ({round(1/p_a, 2)})\n\n"
        f"DOUBLE CHANCE\n"
        f"------------------------\n"
        f"1X : {round(dc_1x*100,1)}%\n"
        f"X2 : {round(dc_x2*100,1)}%\n"
        f"12 : {round(dc_12*100,1)}%\n\n"
        f"Recommandation : {meilleure_dc[0]} a {round(meilleure_dc[1]*100, 1)}%\n\n"
        f"TENDANCES BUTS\n"
        f"------------------------\n"
        f"Plus de 2.5 buts : {round(resultat['over_25']*100,1)}%\n"
        f"Moins de 2.5 buts : {round(resultat['under_25']*100,1)}%\n"
        f"Les 2 marquent : {round(resultat['btts_yes']*100,1)}%\n"
        f"Pas les 2 : {round(resultat['btts_no']*100,1)}%\n\n"
        f"SCORES PROBABLES\n"
        f"------------------------\n"
        f"{scores_txt}\n"
        f"Jouez de maniere responsable."
    )


def enregistrer_prediction_handlers(bot):

    # Prédiction par texte (Équipe A vs Équipe B)
    @bot.message_handler(func=lambda m: m.text and 'vs' in m.text.lower())
    def prediction_texte(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)

        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return

        if not _charger_modele():
            bot.reply_to(message, "Modele non charge. Reessaie plus tard.")
            return

        if not peut_faire_pronostic(user_id):
            bot.reply_to(
                message,
                get_text("limite_atteinte", langue, limite=get_limite_jour(user_id))
            )
            return

        parts = message.text.split('vs' if 'vs' in message.text else 'VS')
        if len(parts) < 2:
            bot.reply_to(message, get_text("demande_affiche", langue))
            return

        resultat = predire_match(parts[0].strip(), parts[1].strip())

        if "erreur" in resultat:
            bot.reply_to(message, get_text("erreur_equipe", langue, erreur=resultat['erreur']))
            return

        bulletin = _formater_bulletin(resultat, langue)
        bot.reply_to(message, bulletin)

        sauvegarder_historique(
            resultat['home_team'], resultat['away_team'],
            resultat['p_h'], resultat['p_d'], resultat['p_a'],
            resultat['best_score'][0], resultat['best_score'][1]
        )

        incrementer_compteur(user_id)
