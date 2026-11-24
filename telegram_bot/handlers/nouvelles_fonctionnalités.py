# telegram_bot/handlers/nouvelles_fonctionnalités.py
"""
Handlers Telegram pour les nouvelles fonctionnalités métier.

Ces handlers font le pont entre les commandes Telegram et les services
dans core/services/. Ils se limitent au formatage et aux callbacks,
conformément à l'architecture (pas de SQL métier dans les handlers).

Chaque handler est enregistré via :func:`enregistrer_handlers_nouvelles_fonctionnalités`
depuis `telegram_bot/handlers/__init__.py` ou `app.py`.
"""

from __future__ import annotations

from typing import Any

import telebot
from telebot.types import Message

from core.services.prediction import ServicePrediction
from core.services.paris import ServiceParis
from core.services.risque import ServiceRisque
from core.services.paiement import ServicePaiement
from core.services.utilisateurs import ServiceUtilisateurs
from core.services.admin import ServiceAdmin
from core.utils.logs import log_info, log_error


class HandlersNouvellesFonctionnalités:
    """Regroupe tous les handlers Telegram des nouvelles fonctionnalités."""

    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.prediction = ServicePrediction()
        self.paris = ServiceParis()
        self.risque = ServiceRisque()
        self.paiement = ServicePaiement()
        self.utilisateurs = ServiceUtilisateurs()
        self.admin = ServiceAdmin()

    def enregistrer(self) -> None:
        """Enregistre tous les handlers sur le bot."""
        self.bot.message_handler(commands=["prono"])(self.cmd_prono)
        self.bot.message_handler(commands=["valuebet"])(self.cmd_valuebet)
        self.bot.message_handler(commands=["cashout"])(self.cmd_cashout)
        self.bot.message_handler(commands=["kelly"])(self.cmd_kelly)
        self.bot.message_handler(commands=["paiement"])(self.cmd_paiement)
        self.bot.message_handler(commands=["premium"])(self.cmd_premium)
        self.bot.message_handler(commands=["admin_catalogue"])(self.cmd_admin_catalogue)
        self.bot.message_handler(commands=["admin_status"])(self.cmd_admin_status)
        self.bot.message_handler(commands=["meteo"])(self.cmd_meteo)
        log_info("Handlers nouvelles fonctionnalités enregistrés", "HANDLERS")

    # ------------------------------------------------------------------
    # Commandes utilisateur
    # ------------------------------------------------------------------

    def cmd_prono(self, message: Message) -> None:
        """/prono Equipe1 vs Equipe2 [cote1 coteN cote2]"""
        try:
            texte = message.text or ""
            parties = texte.split()
            if len(parties) < 3:
                self.bot.reply_to(
                    message,
                    "Usage : /prono Equipe1 vs Equipe2 [cote1 coteN cote2]\n"
                    "Exemple : /prono Real Madrid vs Barcelone 2.10 3.40 3.80",
                )
                return

            # Parsing simple : "Equipe1 vs Equipe2" puis cotes optionnelles
            vs_index = parties.index("vs") if "vs" in parties else -1
            if vs_index == -1 or vs_index < 2:
                self.bot.reply_to(message, "Format attendu : Equipe1 vs Equipe2")
                return

            home_team = " ".join(parties[1:vs_index])
            away_team = " ".join(parties[vs_index + 1:])

            cotes_book: dict[str, float] | None = None
            cotes_args = [p for p in parties if p.replace(".", "", 1).isdigit()]
            if len(cotes_args) >= 3:
                cotes_book = {
                    "h": float(cotes_args[0]),
                    "d": float(cotes_args[1]),
                    "a": float(cotes_args[2]),
                }

            resultat = self.prediction.predire(home_team, away_team, cotes_book=cotes_book)

            if "erreur" in resultat:
                self.bot.reply_to(message, f"❌ {resultat['erreur']}")
                return

            reponse = (
                f"⚽ <b>{resultat['home_team']} vs {resultat['away_team']}</b>\n"
                f"🏆 {resultat['competition']}\n\n"
                f"📊 <b>Probabilités IA :</b>\n"
                f"• Domicile : {resultat['p_h']*100:.1f}%\n"
                f"• Nul : {resultat['p_d']*100:.1f}%\n"
                f"• Extérieur : {resultat['p_a']*100:.1f}%\n"
                f"🎯 Favori : {resultat['favori']} (confiance : {resultat['confiance']*100:.1f}%)\n"
                f"🔀 Double chance : 1X={resultat['dc_1x']*100:.1f}% | X2={resultat['dc_x2']*100:.1f}% | 12={resultat['dc_12']*100:.1f}%\n\n"
            )

            if resultat.get("analyse_pari"):
                ap = resultat["analyse_pari"]
                if ap.get("is_value"):
                    reponse += (
                        f"💎 <b>VALUE BET détecté :</b> {ap['label']}\n"
                        f"   Proba IA : {ap['proba']*100:.1f}% | Cote : {ap['cote_book']}\n"
                        f"   EV : {ap['ev']*100:.1f}%\n\n"
                    )

            reponse += (
                "⚠️ <i>Analyse statistique, pas une garantie de gain. "
                "Ne misez que ce que vous pouvez vous permettre de perdre.</i>"
            )
            self.bot.reply_to(message, reponse, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /prono", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors de la prédiction. Réessayez plus tard.")

    def cmd_valuebet(self, message: Message) -> None:
        """/valuebet proba cote [label]"""
        try:
            parties = (message.text or "").split()
            if len(parties) < 3:
                self.bot.reply_to(message, "Usage : /valuebet probabilite cote [label]\nExemple : /valuebet 0.65 2.10 1")
                return

            proba = float(parties[1])
            cote = float(parties[2])
            label = parties[3] if len(parties) > 3 else None

            verdict = self.paris.analyser_value_bet(proba, cote, label)
            if verdict is None:
                self.bot.reply_to(message, "❌ Données invalides (proba entre 0 et 1, cote > 1.0)")
                return

            if verdict["is_value"]:
                reponse = (
                    f"💎 <b>VALUE BET :</b> {verdict['label']}\n"
                    f"   Proba : {verdict['proba']*100:.1f}% | Cote : {verdict['cote_book']}\n"
                    f"   EV : {verdict['ev']*100:.1f}%\n"
                )
            else:
                reponse = (
                    f"➖ Pas de value bet : {verdict['label']}\n"
                    f"   EV : {verdict['ev']*100:.1f}% (seuil non atteint)\n"
                )
            self.bot.reply_to(message, reponse, parse_mode="HTML")

        except ValueError:
            self.bot.reply_to(message, "❌ Format invalide : proba et cote doivent être des nombres.")
        except Exception as e:
            log_error("Erreur commande /valuebet", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors de l'analyse value bet.")

    def cmd_cashout(self, message: Message) -> None:
        """/cashout mise cote_initiale cote_actuelle [fraction]"""
        try:
            parties = (message.text or "").split()
            if len(parties) < 4:
                self.bot.reply_to(
                    message,
                    "Usage : /cashout mise cote_initiale cote_actuelle [fraction]\n"
                    "Exemple : /cashout 10000 2.50 1.80 [0.5]",
                )
                return

            mise = float(parties[1])
            cote_i = float(parties[2])
            cote_a = float(parties[3])
            fraction = float(parties[4]) if len(parties) > 4 else None

            if fraction is not None:
                res = self.paris.calculer_cashout_partiel(mise, cote_i, cote_a, fraction)
                reponse = (
                    f"💰 <b>Cash-out partiel :</b>\n"
                    f"   Montant encaissé : {res['montant_encaisse']:,.0f} FC\n"
                    f"   Mise restante : {res['mise_restante']:,.0f} FC\n"
                    f"   Bénéfice partiel : {res['benefice_partiel']:,.0f} FC\n"
                )
            else:
                res = self.paris.calculer_cashout(mise, cote_i, cote_a)
                reponse = (
                    f"💰 <b>Cash-out total :</b>\n"
                    f"   Mise : {res['mise']:,.0f} FC\n"
                    f"   Gain potentiel : {res['gain_potentiel']:,.0f} FC\n"
                    f"   Montant cash-out : {res['montant_cashout']:,.0f} FC\n"
                    f"   Bénéfice net : {res['benefice_net']:,.0f} FC\n"
                )
            self.bot.reply_to(message, reponse, parse_mode="HTML")

        except ValueError:
            self.bot.reply_to(message, "❌ Format invalide : tous les paramètres doivent être des nombres.")
        except Exception as e:
            log_error("Erreur commande /cashout", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors du calcul de cash-out.")

    def cmd_kelly(self, message: Message) -> None:
        """/kelly bankroll proba cote [fraction_kelly]"""
        try:
            parties = (message.text or "").split()
            if len(parties) < 4:
                self.bot.reply_to(
                    message,
                    "Usage : /kelly bankroll proba cote [fraction_kelly]\n"
                    "Exemple : /kelly 100000 0.65 2.10 0.25",
                )
                return

            from core.domaine import Bankroll

            bankroll = Bankroll(user_id=message.from_user.id, montant_total=float(parties[1]))
            proba = float(parties[2])
            cote = float(parties[3])
            fraction = float(parties[4]) if len(parties) > 4 else 0.25

            res = self.risque.calculer_mise_kelly(bankroll, proba, cote, fraction)

            reponse = (
                f"📊 <b>Kelly fractionné :</b>\n"
                f"   Mise Kelly : {res['mise_kelly']:,.0f} FC\n"
                f"   Mise recommandée : {res['mise_recommandee']:,.0f} FC\n"
                f"   Plafond bankroll : {res['plafond']:,.0f} FC\n"
                f"   Autorisée : {'Oui' if res['autorisee'] else 'Non'}\n"
            )
            self.bot.reply_to(message, reponse, parse_mode="HTML")

        except ValueError as e:
            self.bot.reply_to(message, f"❌ {str(e)}")
        except Exception as e:
            log_error("Erreur commande /kelly", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors du calcul Kelly.")

    def cmd_paiement(self, message: Message) -> None:
        """/paiement operateur montant reference numero"""
        try:
            parties = (message.text or "").split()
            if len(parties) < 5:
                self.bot.reply_to(
                    message,
                    "Usage : /paiement operateur montant reference numero\n"
                    "Exemple : /paiement airtel 5000 REF123 0812345678",
                )
                return

            operateur = parties[1]
            montant = int(parties[2])
            reference = parties[3]
            numero = parties[4]

            res = self.paiement.verifier_paiement(operateur, montant, reference, numero)
            if res["valide"]:
                reponse = f"✅ Paiement vérifié : {res['montant']} FC via {res['operateur']} (ref: {res['reference']})"
            else:
                reponse = f"❌ Paiement non vérifié : {res.get('erreur', 'inconnu')}"

            self.bot.reply_to(message, reponse)

        except ValueError:
            self.bot.reply_to(message, "❌ Format invalide : montant et référence requis.")
        except Exception as e:
            log_error("Erreur commande /paiement", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors de la vérification de paiement.")

    def cmd_premium(self, message: Message) -> None:
        """/premium : activer l'essai Premium 24h"""
        try:
            res = self.paiement.essai_premium_24h(message.from_user.id)
            self.bot.reply_to(message, f"✅ {res['message']}")
        except Exception as e:
            log_error("Erreur commande /premium", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors de l'activation Premium.")

    def cmd_admin_catalogue(self, message: Message) -> None:
        """/admin_catalogue : statut des fonctionnalités (admin seulement)"""
        # Vérification simplifiée de l'admin (à renforcer via users/admin.py)
        statut = self.admin.get_statut_fonctionnalites()
        total = len(statut)
        complete = sum(1 for v in statut.values() if v["pret"])
        partie = sum(1 for v in statut.values() if v["statut_impl"] == "partielle")
        non_impl = sum(1 for v in statut.values() if v["statut_impl"] == "a_implanter")

        reponse = (
            f"📊 <b>Catalogue des fonctionnalités :</b>\n"
            f"   Total : {total}\n"
            f"   ✅ Complètes : {complete}\n"
            f"   🔧 Partielles : {partie}\n"
            f"   ⏳ À implanter : {non_impl}\n\n"
            f"Utilisez /admin_status pour plus de détails."
        )
        self.bot.reply_to(message, reponse, parse_mode="HTML")

    def cmd_admin_status(self, message: Message) -> None:
        """/admin_status : dashboard administrateur"""
        dashboard = self.admin.get_dashboard()
        reponse = (
            f"🖥️ <b>Dashboard Admin :</b>\n"
            f"   Utilisateurs : {dashboard.get('utilisateurs', {})}\n"
            f"   Pronostics du jour : {dashboard.get('pronostics_du_jour', {})}\n"
            f"   Paiements en attente : {dashboard.get('paiements_en_attente', 0)}\n"
            f"   Note : {dashboard.get('note', '')}"
        )
        self.bot.reply_to(message, reponse, parse_mode="HTML")

    def cmd_meteo(self, message: Message) -> None:
        """/meteo Ville : conditions météo pour un match"""
        try:
            parties = (message.text or "").split()
            if len(parties) < 2:
                self.bot.reply_to(message, "Usage : /meteo Ville\nExemple : /meteo Kinshasa")
                return

            ville = " ".join(parties[1:])
            from core.adaptateurs.meteo import AdaptateurMeteo
            meteo = AdaptateurMeteo()
            succes, donnees, erreur = meteo.get_meteo(ville)

            if succes:
                reponse = (
                    f"🌤️ <b>Météo à {ville} :</b>\n"
                    f"   Température : {donnees.get('temperature')}°C\n"
                    f"   Condition : {donnees.get('condition')}\n"
                    f"   Humidité : {donnees.get('humidite')}%\n"
                    f"   Pluie (1h) : {donnees.get('pluie')} mm\n"
                    f"   Vent : {donnees.get('vent')} km/h\n"
                )
            else:
                reponse = f"❌ {erreur}"

            self.bot.reply_to(message, reponse, parse_mode="HTML")

        except Exception as e:
            log_error("Erreur commande /meteo", "HANDLERS", exception=e)
            self.bot.reply_to(message, "❌ Erreur lors de la récupération météo.")


def enregistrer_handlers_nouvelles_fonctionnalités(bot: telebot.TeleBot) -> HandlersNouvellesFonctionnalités:
    """Point d'entrée pour enregistrer tous les handlers des nouvelles fonctionnalités.

    Args:
        bot: Instance du bot Telegram (pyTelegramBotAPI TeleBot).

    Returns:
        L'instance des handlers (pour accès aux services si nécessaire).
    """
    handlers = HandlersNouvellesFonctionnalités(bot)
    handlers.enregistrer()
    return handlers
