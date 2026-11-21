# telegram_bot/consultation_handlers.py
"""
Handlers des commandes de consultation :

/fiabilite, /serie, /piege, /comparer, /meteo, /favoris, /cotes,
/cashout, /bankroll (/mise), /preuves, /devise, /codepromo, /utilisercode.
"""

import telebot
from core.consultation import (
    calculer_fiabilite_par_championnat,
    formater_fiabilite,
    calculer_serie_equipe,
    formater_serie,
    detecter_piege,
)
from core.comparateur import analyser_domicile_exterieur, formater_comparateur
from core.meteo import obtenir_meteo_reelle, obtenir_ville_equipe, formater_alerte_meteo
from core.equipes_favorites import ajouter_favori, supprimer_favori, lister_favoris
from core.bookmakers import get_cotes_match, formater_comparateur_bookmakers
from core.cashout import get_cote_actuelle, simuler_cashout, formater_cashout
from core.bankroll import set_bankroll, get_bankroll, calculer_mise, formater_bankroll
from core.utils.logs import log_info, log_error, log_warning
from users.admin import est_administrateur
from users.db import db_fetchall, db_execute, db_fetchone
from users.credits import crediter_premium, deja_credite
from core.codes_promo import creer_code_promo, valider_code_promo
from core.devises import formater_prix, get_taux_change


DEVISES_VALIDES = ("CDF", "USD", "EUR")


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
                from core.cotes_historiques import enregistrer_snapshot, detecter_chute
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


def enregistrer_preuves_handlers(bot):

    @bot.message_handler(commands=['preuves'])
    def cmd_preuves(message):
        user_id = message.from_user.id
        try:
            if not est_administrateur(user_id):
                log_warning(message="Tentative d'accès à /preuves refusée", module="PREUVES", user_context={"user_id": user_id})
                bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
                return

            resultats = db_fetchall(
                "SELECT est_gagnant FROM resultats_pronostics ORDER BY id DESC LIMIT 30",
                db_context={'table': 'resultats_pronostics', 'operation': 'preuves'},
            )

            if not resultats:
                bot.reply_to(message, "📊 HISTORIQUE VÉRIFIABLE\n\nAucun résultat enregistré pour le moment.", parse_mode='HTML')
                log_info("Commande /preuves : aucun résultat", "PREUVES", user_context={"user_id": user_id})
                return

            # row[0] fonctionne pour un tuple comme pour un sqlite3.Row ;
            # les valeurs NULL ne valent ni 1 ni 0 et sont donc ignorées.
            gagnes = sum(1 for row in resultats if row[0] == 1)
            perdus = sum(1 for row in resultats if row[0] == 0)
            total = gagnes + perdus
            taux = round((gagnes / total) * 100) if total > 0 else 0

            texte = (
                "📊 HISTORIQUE VÉRIFIABLE\n\n"
                "30 derniers jours :\n"
                f"✅ Gagnés : {gagnes}\n"
                f"❌ Perdus : {perdus}\n"
                f"🎯 Taux de réussite : {taux}%\n\n"
                "Ces résultats sont issus de la base de données et ne peuvent pas être modifiés."
            )

            try:
                bot.reply_to(message, texte, parse_mode='HTML')
                log_info("Commande /preuves envoyée", "PREUVES", user_context={"user_id": user_id})
            except Exception as e:
                log_warning(message=f"Erreur d'envoi du message /preuves pour {user_id}", module="PREUVES", user_context={"user_id": user_id}, exception=e)
        except Exception as e:
            log_warning(message=f"Erreur commande /preuves pour {user_id}", module="PREUVES", user_context={"user_id": user_id}, exception=e)


def _assurer_colonne_devise():
    """Crée la colonne `devise` si elle n'existe pas (ALTER TABLE local).

    On interroge la forme table-valuee de PRAGMA table_info('utilisateurs')
    pour rester compatible avec db_fetchone (une seule ligne renvoyee).
    """
    try:
        row = db_fetchone(
            "SELECT COUNT(*) FROM pragma_table_info('utilisateurs') "
            "WHERE name = 'devise'"
        )
        if row and row[0]:
            return True

        resultat = db_execute(
            "ALTER TABLE utilisateurs ADD COLUMN devise TEXT DEFAULT 'CDF'",
            db_context={"table": "utilisateurs", "operation": "add_column_devise"},
        )
        if resultat is not None:
            log_info("Colonne devise ajoutee a la table utilisateurs", module="DEVISES")
        return True
    except Exception as e:
        # La colonne peut deja exister (course entre deux appels) : on ignore.
        if "duplicate column" in str(e).lower():
            return True
        log_error(
            message="Impossible d'assurer la colonne devise",
            module="DEVISES",
            exception=e,
        )
        return False


def set_devise(user_id, devise):
    """Enregistre la devise preferee d'un utilisateur."""
    if devise not in DEVISES_VALIDES:
        log_error(
            message="Devise non supportee",
            module="DEVISES",
            user_context={"user_id": user_id},
            extra={"devise_demandee": devise},
        )
        return False

    rowcount = db_execute(
        "UPDATE utilisateurs SET devise = ? WHERE user_id = ?",
        params=[devise, user_id],
        db_context={"table": "utilisateurs", "operation": "set_devise"},
    )
    return rowcount is not None and rowcount > 0


def get_devise(user_id):
    """Retourne la devise preferee d'un utilisateur (defaut : CDF)."""
    try:
        row = db_fetchone(
            "SELECT devise FROM utilisateurs WHERE user_id = ?",
            params=[user_id],
            db_context={"table": "utilisateurs", "operation": "get_devise"},
        )
        devise = row[0] if row and row[0] else "CDF"
        if devise not in DEVISES_VALIDES:
            return "CDF"
        return devise
    except Exception as e:
        log_error(
            message="Impossible de recuperer la devise",
            module="DEVISES",
            user_context={"user_id": user_id},
            exception=e,
        )
        return "CDF"


def _clavier_devises():
    """Construit le clavier inline des 3 devises proposees."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        telebot.types.InlineKeyboardButton("🇨🇩 CDF", callback_data="dev|CDF"),
        telebot.types.InlineKeyboardButton("🇺🇸 USD", callback_data="dev|USD"),
        telebot.types.InlineKeyboardButton("🇪🇺 EUR", callback_data="dev|EUR"),
    )
    return markup


def _texte_devise(devise):
    """Texte d'invitation affichant la devise courante et un exemple."""
    return (
        "💱 <b>Votre devise préférée</b>\n\n"
        f"Devise actuelle : <b>{devise}</b>\n"
        f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>\n\n"
        "Choisissez votre devise ci-dessous :"
    )


def _ligne_taux(devise):
    """Retourne la ligne d'affichage du taux, ou un avertissement si indisponible."""
    taux = get_taux_change(devise)
    if taux is None:
        return f"Taux : <i>indisponible pour le moment</i>"
    return f"Taux : 1 {devise} = {taux} CDF"


def enregistrer_devises_handlers(bot):
    """Enregistre les handlers de la commande /devise."""

    @bot.message_handler(commands=['devise'])
    def commande_devise(message):
        user_id = message.from_user.id
        try:
            _assurer_colonne_devise()
            devise = get_devise(user_id)
            bot.send_message(
                message.chat.id,
                _texte_devise(devise),
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as e:
            log_error(
                message="Erreur lors de la commande /devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
            )

    @bot.message_handler(func=lambda m: m.text == "💎 Devise")
    def bouton_devise(message):
        user_id = message.from_user.id
        try:
            _assurer_colonne_devise()
            devise = get_devise(user_id)
            bot.send_message(
                message.chat.id,
                _texte_devise(devise),
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as e:
            log_error(
                message="Erreur lors du bouton Devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("dev|"))
    def callback_devise(call):
        user_id = call.from_user.id
        try:
            _assurer_colonne_devise()
            devise = call.data.split("|", 1)[1]
            if not set_devise(user_id, devise):
                bot.answer_callback_query(call.id, "❌ Devise invalide")
                return

            bot.answer_callback_query(call.id, "✅ Devise enregistrée")
            texte = (
                "💱 <b>Devise enregistrée</b>\n\n"
                f"Devise : <b>{devise}</b>\n"
                f"{_ligne_taux(devise)}\n"
                f"Exemple : 10 000 CDF = <b>{formater_prix(10000, devise)}</b>"
            )
            bot.edit_message_text(
                texte,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_clavier_devises(),
                parse_mode="HTML",
            )
        except Exception as e:
            log_error(
                message="Erreur lors du callback devise",
                module="DEVISES",
                user_context={"user_id": user_id},
                exception=e,
            )



def enregistrer_codes_promo_handlers(bot):

    @bot.message_handler(commands=['codepromo'])
    def cmd_codepromo(message):
        user_id = message.from_user.id

        if not est_administrateur(user_id):
            bot.reply_to(message, "⛔ Commande réservée aux administrateurs.")
            return

        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(
                message,
                "⚠️ <b>Format incorrect.</b>\n\n"
                "Utilise : <code>/codepromo CODE TYPE VALEUR [LIMITE] [JOURS]</code>\n\n"
                "• <b>TYPE</b> : <code>pourcentage</code> ou <code>fixe</code>\n"
                "• <b>VALEUR</b> : nombre positif\n"
                "• <b>LIMITE</b> : nombre d'utilisations max (0 = illimité, défaut)\n"
                "• <b>JOURS</b> : jours Premium offerts (défaut 1)\n\n"
                "Exemples :\n"
                "<code>/codepromo CAN2026 pourcentage 30 100</code>\n"
                "<code>/codepromo BIENVENUE fixe 2000</code>\n"
                "<code>/codepromo VIP pourcentage 50 10 7</code>",
                parse_mode="HTML"
            )
            return

        code = args[1].upper()
        type_reduction = args[2].lower()

        try:
            valeur = float(args[3])
            limite = int(args[4]) if len(args) > 4 else 0
            jours = int(args[5]) if len(args) > 5 else 1
        except ValueError:
            bot.reply_to(message, "❌ VALEUR, LIMITE et JOURS doivent être des nombres.")
            return

        if type_reduction not in ("pourcentage", "fixe"):
            bot.reply_to(message, "❌ TYPE doit être 'pourcentage' ou 'fixe'.")
            return

        succes = creer_code_promo(
            code, type_reduction, valeur,
            limite_utilisation=limite,
            jours_premium=jours,
        )

        if succes:
            bot.reply_to(
                message,
                f"✅ Code <b>{code}</b> créé !\n"
                f"Type : {type_reduction}\n"
                f"Valeur : {valeur}\n"
                f"Limite : {'Illimitée' if limite == 0 else limite}\n"
                f"Jours Premium offerts : {jours}",
                parse_mode="HTML"
      )
            log_info(
                f"Code promo {code} créé par admin {user_id}",
                "CODES_PROMO",
                user_context={"user_id": user_id},
                extra={"code": code, "type": type_reduction, "jours": jours},
            )
        else:
            bot.reply_to(
                message,
                f"❌ Impossible de créer le code {code}.\n"
                f"Il existe peut-être déjà, ou les paramètres sont invalides."
            )


def enregistrer_utilisation_code_handlers(bot):

    @bot.message_handler(commands=['utilisercode'])
    def cmd_utilisercode(message):
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2:
            bot.reply_to(
                message,
                "⚠️ Utilise : <code>/utilisercode TON_CODE</code>",
                parse_mode="HTML"
            )
            return

        code = args[1].upper()

        # Un utilisateur ne peut utiliser un même code qu'une seule fois.
        # Vérifié AVANT valider_code_promo, qui incrémente le compteur du code.
        if deja_credite(f"codepromo:{code}:{user_id}"):
            bot.reply_to(message, "❌ Tu as déjà utilisé ce code.")
            return

        resultat = valider_code_promo(code, user_id)

        if not resultat.get("valide"):
            bot.reply_to(
                message,
                f"❌ {resultat.get('message', 'Code invalide.')}"
            )
            return

        jours = resultat.get("jours_premium", 1)
        type_reduction = resultat.get("type_reduction")
        valeur = resultat.get("valeur")

        # Application réelle des jours Premium
        try:
            if crediter_premium(f"codepromo:{code}:{user_id}", user_id, jours, "codepromo") == "echec":
                log_error(
                    message="Code validé mais ajout Premium échoué",
                    module="CODES_PROMO",
                    user_context={"user_id": user_id},
                    extra={"code": code, "jours": jours},
                )
                bot.reply_to(
                    message,
                    "❌ Code validé mais l'ajout Premium a échoué. "
                    "Contacte l'admin avec ce code : " + code
                )
                return
        except Exception as e:
            log_error(
                message="Erreur application code promo",
                module="CODES_PROMO",
                user_context={"user_id": user_id},
                exception=e,
            )
            bot.reply_to(
                message,
                "❌ Code validé mais erreur lors de l'application. "
                "Contacte l'admin avec ce code : " + code
            )
            return

        bot.reply_to(
            message,
            f"✅ Code <b>{code}</b> validé !\n\n"
            f"🎁 +{jours} jour(s) Premium offert(s)\n"
            f"Réduction commerciale : {valeur} ({type_reduction})",
            parse_mode="HTML"
        )
        log_info(
            f"Code {code} utilisé par {user_id} (+{jours}j)",
            "CODES_PROMO",
            user_context={"user_id": user_id},
            extra={"code": code, "jours": jours},
        )
