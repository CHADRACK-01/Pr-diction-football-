# telegram_bot/consultation_handlers.py
"""
Handlers des commandes de consultation :

/fiabilite, /serie, /piege, /comparer, /meteo, /favoris, /cotes,
/cashout, /bankroll (/mise), /preuves, /devise, /codepromo, /utilisercode.
"""

from core.data.consultation import (
    calculer_fiabilite_par_championnat,
    formater_fiabilite,
    calculer_serie_equipe,
    formater_serie,
    detecter_piege,
)
from core.data.comparateur import analyser_domicile_exterieur, formater_comparateur
from core.data.meteo import obtenir_meteo_reelle, obtenir_ville_equipe, formater_alerte_meteo
from core.engagement.equipes_favorites import ajouter_favori, supprimer_favori, lister_favoris
from core.bookmakers import get_cotes_match, formater_comparateur_bookmakers
from core.betting.cashout import get_cote_actuelle, simuler_cashout, formater_cashout
from core.betting.bankroll import set_bankroll, get_bankroll, calculer_mise, formater_bankroll
from core.utils.logs import log_info, log_error, log_warning
from users.admin import est_administrateur
from users.db import db_fetchall
from users.credits import crediter_premium, deja_credite
from core.engagement.codes_promo import creer_code_promo, valider_code_promo, annuler_utilisation_promo
from telegram_bot.consultation.codes_promo import (
    enregistrer_codes_promo_handlers,
    enregistrer_utilisation_code_handlers,
)
from telegram_bot.consultation.preuves import enregistrer_preuves_handlers

# Compatibilité historique : les fonctions devise sont maintenues sous l'ancien nom.
from telegram_bot.consultation.devises import (
    DEVISES_VALIDES,
    _assurer_colonne_devise,
    _clavier_devises,
    _ligne_taux,
    _texte_devise,
    enregistrer_devises_handlers,
    get_devise,
    set_devise,
)


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


def enregistrer_favoris_handlers(bot):

    @bot.message_handler(commands=['favoris'])
    def cmd_favoris(message):
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            # Afficher la liste des favoris
            favoris = lister_favoris(user_id)
            if not favoris:
                texte = "📋 <b>TES ÉQUIPES FAVORITES</b>\n\n"
                texte += "Tu n'as pas encore d'équipe favorite.\n\n"
                texte += "Utilise : <code>/favoris ajouter NOM_EQUIPE</code>"
            else:
                texte = "📋 <b>TES ÉQUIPES FAVORITES</b>\n\n"
                for i, equipe in enumerate(favoris, 1):
                    texte += f"{i}. {equipe}\n"
                texte += f"\n📊 {len(favoris)}/5 équipes\n"
                texte += "\nPour supprimer : <code>/favoris supprimer NOM_EQUIPE</code>"

            bot.reply_to(message, texte, parse_mode="HTML")
            return

        action = args[1].split(maxsplit=1)
        if len(action) < 2:
            bot.reply_to(message, "❌ Format : <code>/favoris ajouter/supprimer NOM_EQUIPE</code>", parse_mode="HTML")
            return

        commande = action[0].lower()
        equipe = action[1].strip()

        if commande == "ajouter":
            succes, msg = ajouter_favori(user_id, equipe)
            bot.reply_to(message, msg)
        elif commande == "supprimer":
            succes, msg = supprimer_favori(user_id, equipe)
            bot.reply_to(message, msg)
        else:
            bot.reply_to(message, "❌ Commande inconnue. Utilise 'ajouter' ou 'supprimer'.")


def enregistrer_bookmakers_handlers(bot):

    @bot.message_handler(commands=['cotes'])
    def cmd_cotes(message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/cotes EQUIPE1 vs EQUIPE2 [SPORT]</code>\n"
                "Exemple : <code>/cotes Chelsea vs Arsenal</code>\n"
                "Sports : <code>soccer_epl</code> (défaut), <code>soccer_spain_la_liga</code>, etc.",
                parse_mode="HTML"
            )
            return

        try:
            parties = args[1].split(" vs ")
            if len(parties) != 2:
                bot.reply_to(message, "❌ Format : <code>/cotes Equipe1 vs Equipe2</code>", parse_mode="HTML")
                return

            home_team = parties[0].strip()
            
            # On sépare l'équipe extérieure du sport éventuel
            away_parts = parties[1].split()
            away_team = away_parts[0].strip()
            sport = away_parts[1] if len(away_parts) > 1 else "soccer_epl"

            bot.reply_to(message, f"⏳ Récupération des cotes pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            resultats = get_cotes_match(home_team, away_team, sport)
            # Historique horodaté : aucun appel API en plus, on garde ce qui vient d'être lu
            alertes_chute = []
            try:
                from core.data.cotes_historiques import enregistrer_snapshot, detecter_chute
                enregistrer_snapshot(home_team, away_team, resultats)
                # Chute de cote depuis la dernière observation enregistrée, par bookmaker
                for bk in sorted({str(r.get("bookmaker", "inconnu")) for r in resultats or []}):
                    chute = detecter_chute(home_team, away_team, bk)
                    if chute and chute["chutes"]:
                        alertes_chute.append((bk, chute))
            except Exception as e_hist:
                log_error("Historique des cotes non enregistré", "BOOKMAKERS", exception=e_hist)
            
            texte = formater_comparateur_bookmakers(home_team, away_team, resultats)
            if alertes_chute:
                lignes = ["\n📉 <b>Chute de cote détectée</b>"]
                for bk, chute in alertes_chute:
                    for issue in chute["chutes"]:
                        var = chute["variations"][issue]
                        nom = {"home": home_team, "draw": "Nul", "away": away_team}[issue]
                        lignes.append(f"• {bk} : {nom} −{var * 100:.1f} % depuis la dernière observation")
                texte += "\n".join(lignes)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /cotes", "BOOKMAKERS", exception=e)
            bot.reply_to(message, "❌ Erreur lors de l'analyse des cotes.")


def enregistrer_cashout_handlers(bot):

    @bot.message_handler(commands=['cashout'])
    def cmd_cashout(message):
        args = message.text.split()
        
        if len(args) < 5:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/cashout EQUIPE1 vs EQUIPE2 MISE COTE_INITIALE</code>\n"
                "Exemple : <code>/cashout Chelsea vs Arsenal 10000 2.50</code>",
                parse_mode="HTML"
            )
            return

        try:
            # Récupérer les équipes (les 3 premiers mots après la commande)
            match_str = " ".join(args[1:4])  # Chelsea vs Arsenal
            if " vs " not in match_str.lower():
                bot.reply_to(message, "❌ Format : <code>/cashout Equipe1 vs Equipe2 MISE COTE</code>", parse_mode="HTML")
                return

            equipes = match_str.split(" vs ")
            home_team = equipes[0].strip()
            away_team = equipes[1].strip()

            mise = float(args[4])
            cote_initiale = float(args[5]) if len(args) > 5 else 2.00

            bot.reply_to(message, f"⏳ Calcul du cash-out pour <b>{home_team} vs {away_team}</b>...", parse_mode="HTML")

            # Récupérer la cote actuelle
            cote_actuelle = get_cote_actuelle(home_team, away_team)
            
            if cote_actuelle is None:
                bot.reply_to(message, "❌ Impossible de récupérer la cote actuelle. Vérifie le nom des équipes ou le sport.")
                return

            # Calculer le cash-out
            cashout = simuler_cashout(mise, cote_initiale, cote_actuelle)

            texte = formater_cashout(home_team, away_team, mise, cote_initiale, cote_actuelle, cashout)
            bot.reply_to(message, texte, parse_mode="HTML")

        except ValueError:
            bot.reply_to(message, "❌ La mise et la cote doivent être des nombres.")
        except Exception as e:
            log_error("Erreur commande /cashout", "CASHOUT", exception=e)
            bot.reply_to(message, "❌ Erreur lors du calcul.")


def enregistrer_bankroll_handlers(bot):

    @bot.message_handler(commands=['bankroll'])
    def cmd_bankroll(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2:
            # Afficher la bankroll actuelle
            bankroll = get_bankroll(user_id)
            if not bankroll:
                bot.reply_to(
                    message,
                    "⚠️ Tu n'as pas encore défini ta bankroll.\n\n"
                    "Utilise : <code>/bankroll MONTANT [STRATEGIE]</code>\n"
                    "Exemples :\n"
                    "<code>/bankroll 50000</code>\n"
                    "<code>/bankroll 50000 fixe</code>\n"
                    "<code>/bankroll 50000 kelly_fractionne</code>",
                    parse_mode="HTML"
                )
            else:
                texte = f"💰 <b>TA BANKROLL</b>\n\n"
                texte += f"💵 Montant : {bankroll['montant_total']:,.0f} CDF\n"
                texte += f"📊 Stratégie : {bankroll['strategie']}\n"
                texte += f"📈 Pourcentage de mise : {bankroll['pourcentage_mise']}%"
                bot.reply_to(message, texte, parse_mode="HTML")
            return

        try:
            montant = float(args[1])
            strategie = args[2].lower() if len(args) > 2 else "kelly_fractionne"

            if strategie not in ("kelly_fractionne", "fixe"):
                bot.reply_to(message, "❌ Stratégie invalide. Utilise 'kelly_fractionne' ou 'fixe'.")
                return

            succes = set_bankroll(user_id, montant, strategie)
            
            if succes:
                bot.reply_to(
                    message,
                    f"✅ Bankroll mise à jour !\n\n"
                    f"💵 Montant : {montant:,.0f} CDF\n"
                    f"📊 Stratégie : {strategie}\n\n"
                    f"Utilise <code>/mise PROBA COTE</code> pour calculer ta prochaine mise.",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(message, "❌ Erreur lors de l'enregistrement.")

        except ValueError:
            bot.reply_to(message, "❌ Le montant doit être un nombre.")

    @bot.message_handler(commands=['mise'])
    def cmd_mise(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 3:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/mise PROBA COTE</code>\n"
                "Exemple : <code>/mise 0.65 2.10</code>",
                parse_mode="HTML"
            )
            return

        try:
            proba = float(args[1])
            cote = float(args[2])

            if proba > 1:
                proba = proba / 100  # Convertir 65 en 0.65

            bankroll = get_bankroll(user_id)
            if not bankroll:
                bot.reply_to(message, "❌ Tu dois d'abord définir ta bankroll avec /bankroll MONTANT")
                return

            mise, explication = calculer_mise(user_id, proba, cote)
            texte = formater_bankroll(bankroll, mise, explication)
            
            bot.reply_to(message, texte, parse_mode="HTML")

        except ValueError:
            bot.reply_to(message, "❌ La proba et la cote doivent être des nombres.")


# Adaptateur historique : preuve et codes promo ont été extraits vers
# telegram_bot.consultation.preuves et telegram_bot.consultation.codes_promo.
