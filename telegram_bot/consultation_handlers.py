# telegram_bot/consultation_handlers.py
"""
Handlers des commandes de consultation :
/fiabilite, /serie, /piege, /comparer et /meteo.
"""

import telebot
from core.fiabilite import calculer_fiabilite_par_championnat, formater_fiabilite
from core.momentum import calculer_serie_equipe, formater_serie
from core.pieges import detecter_piege
from core.comparateur import analyser_domicile_exterieur, formater_comparateur
from core.meteo import obtenir_meteo_reelle, obtenir_ville_equipe, formater_alerte_meteo
from core.utils.logs import log_info, log_error


def enregistrer_fiabilite_handlers(bot):

    @bot.message_handler(commands=['fiabilite'])
    def cmd_fiabilite(message):
        bot.reply_to(message, "⏳ Analyse des résultats par championnat...")

        try:
            resultats = calculer_fiabilite_par_championnat()
            texte = formater_fiabilite(resultats)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error("Erreur commande /fiabilite", "FIABILITE", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")


def enregistrer_momentum_handlers(bot):

    @bot.message_handler(commands=['serie'])
    def cmd_serie(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/serie NOM_EQUIPE</code>\n"
                "Exemple : <code>/serie Bayern Munich</code>",
                parse_mode="HTML"
            )
            return

        nom_equipe = args[1].strip()
        bot.reply_to(message, f"⏳ Analyse de la série de <b>{nom_equipe}</b>...", parse_mode="HTML")

        try:
            resultat = calculer_serie_equipe(nom_equipe)
            texte = formater_serie(nom_equipe, resultat)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error(f"Erreur calcul série pour {nom_equipe}", "MOMENTUM", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")


def enregistrer_pieges_handlers(bot):

    @bot.message_handler(commands=['piege'])
    def cmd_piege(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/piege EQUIPE1 vs EQUIPE2</code>\n"
                "Exemple : <code>/piege Real Madrid vs Barcelona</code>",
                parse_mode="HTML"
            )
            return

        try:
            match = args[1].split(" vs ")
            if len(match) != 2:
                bot.reply_to(message, "❌ Format : <code>/piege Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = match[0].strip()
            away_team = match[1].strip()

            bot.reply_to(message, f"⏳ Analyse de <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            resultat = detecter_piege(home_team, away_team)
            
            if resultat["est_piege"]:
                texte = f"⚠️ <b>ATTENTION : MATCH PIÈGE</b>\n\n"
                texte += f"🏟️ {home_team} vs {away_team}\n\n"
                texte += f"🔍 <b>Raisons :</b>\n{resultat['raison']}\n\n"
                texte += "💡 <i>Sois prudent sur ce match.</i>"
            else:
                texte = f"✅ <b>Match sans piège détecté</b>\n\n"
                texte += f"🏟️ {home_team} vs {away_team}\n\n"
                texte += "💡 <i>Ce match ne présente pas de risque particulier.</i>"

            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /piege", "PIEGES", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")


def enregistrer_comparateur_handlers(bot):

    @bot.message_handler(commands=['comparer'])
    def cmd_comparer(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/comparer NOM_EQUIPE</code>\n"
                "Exemple : <code>/comparer Chelsea</code>",
                parse_mode="HTML"
            )
            return

        nom_equipe = args[1].strip()
        bot.reply_to(message, f"⏳ Analyse de <b>{nom_equipe}</b>...", parse_mode="HTML")

        try:
            stats = analyser_domicile_exterieur(nom_equipe)
            texte = formater_comparateur(stats)
            bot.reply_to(message, texte, parse_mode="HTML")
        except Exception as e:
            log_error(f"Erreur commande /comparer pour {nom_equipe}", "COMPARATEUR", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse.")


def enregistrer_meteo_handlers(bot):

    @bot.message_handler(commands=['meteo'])
    def cmd_meteo(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/meteo EQUIPE1 vs EQUIPE2</code>\n"
                "Exemple : <code>/meteo Chelsea vs Arsenal</code>",
                parse_mode="HTML"
            )
            return

        try:
            match = args[1].split(" vs ")
            if len(match) != 2:
                bot.reply_to(message, "❌ Format : <code>/meteo Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = match[0].strip()
            away_team = match[1].strip()

            bot.reply_to(message, f"⏳ Analyse météo pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            # On devine la ville de l'équipe à domicile
            ville = obtenir_ville_equipe(home_team)
            
            # On récupère la vraie météo (ou une valeur neutre)
            meteo = obtenir_meteo_reelle(ville)
            
            texte = formater_alerte_meteo(home_team, away_team, meteo)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /meteo", "METEO", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse météo.")
