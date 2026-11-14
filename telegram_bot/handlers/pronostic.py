# telegram_bot/handlers/pronostic.py
import telebot

from users import (
    get_langue, est_banni, peut_faire_pronostic, get_limite_jour,
    est_administrateur, est_premium, incrementer_compteur,
)
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS
from core.session import (
    creer_session, get_session, maj_session_etape, clear_session,
)
from users.matchs import get_equipes_saison_en_cours
from core.utils.logs import log_info, log_error, log_warning


def _creer_clavier_principal(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("⚽ Faire un Pronostic"),
        telebot.types.KeyboardButton("📅 Matchs du Jour"),
        telebot.types.KeyboardButton("🎟️ Coupons"),
        telebot.types.KeyboardButton("🏆 Top Affiches"),
        telebot.types.KeyboardButton("📜 Historique"),
        telebot.types.KeyboardButton("📊 Statistiques"),
        telebot.types.KeyboardButton("🔔 Notifications"),
        telebot.types.KeyboardButton("💎 Premium"),
        telebot.types.KeyboardButton("🤝 Parrainage"),
        telebot.types.KeyboardButton("🌍 Langue"),
    )
    try:
        if est_administrateur(user_id):
            markup.add(telebot.types.KeyboardButton("👑 Panneau Admin"))
    except Exception:
        pass
    return markup


def _creer_clavier_competitions():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    boutons = []
    for code, nom_propre in CHAMPIONNATS.items():
        infos = INFOS_COMPETITIONS.get(nom_propre, {})
        emoji = infos.get("emoji", "🏆")
        boutons.append(telebot.types.KeyboardButton(f"{emoji} {nom_propre}"))
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))
    return markup


def _creer_clavier_equipes(equipes):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    boutons = [telebot.types.KeyboardButton(eq) for eq in equipes[:60]]
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))
    return markup


def _detecter_competition(texte):
    for code, nom in CHAMPIONNATS.items():
        if nom in texte:
            return code, nom
    return None, None


def _get_contexte_user(message, langue):
    user = message.from_user
    return {
        "user_id": user.id, "user_name": user.first_name or "",
        "username": user.username or "", "chat_id": message.chat.id,
        "langue": langue, "message_text": (message.text or "")[:100],
    }


def enregistrer_pronostic_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "⚽ Faire un Pronostic")
    def handle_pronostic(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message, langue)
        log_info("Menu pronostic demandé", "PRONOSTIC", user_context=ctx)

        try:
            if est_banni(user_id):
                bot.reply_to(message, get_text("banni", langue))
                return
            if not peut_faire_pronostic(user_id):
                limite = get_limite_jour(user_id)
                bot.reply_to(message, get_text("limite_atteinte", langue, limite=limite))
                return
        except Exception as e:
            log_error("Erreur vérification", "PRONOSTIC", user_context=ctx, exception=e)
            return

        try:
            bot.reply_to(message, "⚽ <b>Choisis la compétition</b> :", 
                         reply_markup=_creer_clavier_competitions(), parse_mode="HTML")
        except Exception as e:
            log_error("Erreur affichage compétitions", "PRONOSTIC", user_context=ctx, exception=e)

    @bot.message_handler(func=lambda m: m.text == "↩️ Retour au Menu")
    def retour_menu(message):
        user_id = message.from_user.id
        clear_session(user_id)
        try:
            from telegram_bot.handlers.start import envoyer_menu_principal
            envoyer_menu_principal(message.chat.id, user_id, bot)
        except Exception as e:
            log_error("Erreur retour menu", "PRONOSTIC", exception=e)

    @bot.message_handler(func=lambda m: m.text and _detecter_competition(m.text)[0] is not None)
    def handle_choix_competition(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message, langue)
        comp_code, nom_propre = _detecter_competition(message.text)

        if not comp_code:
            return

        log_info(f"Compétition choisie : {nom_propre}", "PRONOSTIC", user_context=ctx)
        try:
            equipes = get_equipes_saison_en_cours(nom_propre)
        except Exception as e:
            log_error("Erreur récupération équipes", "PRONOSTIC", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la récupération des équipes.")
            return

        if not equipes:
            bot.reply_to(message, f"⚠️ Aucune équipe trouvée pour <b>{nom_propre}</b> cette saison.", parse_mode="HTML")
            return

        if not creer_session(user_id, comp_code, nom_propre, equipes):
            bot.reply_to(message, "❌ Impossible de démarrer la session. Réessaie.")
            return

        bot.send_message(
            message.chat.id,
            f"⚽ Compétition : <b>{nom_propre}</b>\n\n🏠 Sélectionne l'équipe <b>à domicile</b> :",
            reply_markup=_creer_clavier_equipes(equipes), parse_mode="HTML"
        )

    @bot.message_handler(func=lambda m: _est_en_session(m.from_user.id, "domicile"))
    def handle_choix_domicile(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message, langue)
        session = get_session(user_id)
        if not session:
            return

        equipe_dom = (message.text or "").strip()
        if equipe_dom not in session["equipes"]:
            return

        maj_session_etape(user_id, "exterieur", equipe_dom=equipe_dom)
        equipes_ext = [eq for eq in session["equipes"] if eq != equipe_dom]
        
        bot.send_message(
            message.chat.id,
            f"🏠 Domicile : <b>{equipe_dom}</b>\n\n✈️ Sélectionne l'équipe <b>à l'extérieur</b> :",
            reply_markup=_creer_clavier_equipes(equipes_ext), parse_mode="HTML"
        )

    @bot.message_handler(func=lambda m: _est_en_session(m.from_user.id, "exterieur"))
    def handle_choix_exterieur(message):
        user_id = message.from_user.id
        langue = get_langue(user_id)
        ctx = _get_contexte_user(message, langue)
        session = get_session(user_id)
        if not session:
            return

        equipe_ext = (message.text or "").strip()
        if equipe_ext not in session["equipes"] or equipe_ext == session.get("equipe_dom"):
            return

        equipe_dom = session.get("equipe_dom", "")
        comp_code = session["competition"]
        competition_reelle = MAPPING_COMPETITIONS.get(comp_code, comp_code)

        clear_session(user_id)
        bot.send_message(
            message.chat.id,
            f"⏳ Calcul de la prédiction pour <b>{equipe_dom} vs {equipe_ext}</b>...",
            reply_markup=_creer_clavier_principal(user_id), parse_mode="HTML"
        )

        try:
            from core.prediction import predire_match, sauvegarder_historique
            resultat = predire_match(equipe_dom, equipe_ext, competition=competition_reelle)
        except Exception as e:
            log_error("Erreur prédiction", "PRONOSTIC", user_context=ctx, exception=e)
            bot.send_message(message.chat.id, "❌ Erreur lors du calcul.")
            return

        if not resultat or "erreur" in resultat:
            erreur_msg = resultat.get("erreur", "Erreur inconnue") if resultat else "Erreur inconnue"
            bot.send_message(message.chat.id, f"❌ {erreur_msg}")
            return

        # --- ENVOI DU BULLETIN FORMATÉ (HTML) ---
        try:
            from telegram_bot.prediction_handlers import _formater_bulletin_premium, _formater_bulletin_free
            is_prem = est_premium(user_id)
            bulletin = _formater_bulletin_premium(resultat) if is_prem else _formater_bulletin_free(resultat)
            # ⚠️ L'IMPORTANT EST ICI : parse_mode="HTML"
            bot.send_message(message.chat.id, bulletin, parse_mode="HTML")
        except Exception as e:
            log_error("Erreur affichage bulletin", "PRONOSTIC", user_context=ctx, exception=e)
            bot.send_message(message.chat.id, "⚠️ Prédiction calculée mais affichage échoué.")

        # --- SAUVEGARDE HISTORIQUE ---
        try:
            top_scores = resultat.get("top_scores", [(1, 0, 0)])
            best_i, best_j = top_scores[0][0], top_scores[0][1]
            
            sauvegarder_historique(
                resultat["home_team"], resultat["away_team"], competition_reelle,
                resultat["p_h"], resultat["p_d"], resultat["p_a"],
                best_i, best_j
            )
        except Exception as e:
            log_error("Erreur sauvegarde historique", "PRONOSTIC", exception=e)

        # --- COMPTEUR ---
        try:
            incrementer_compteur(user_id)
        except Exception as e:
            log_error("Erreur compteur", "PRONOSTIC", exception=e)


def _est_en_session(user_id, etape):
    try:
        s = get_session(user_id)
        return s is not None and s.get("etape") == etape
    except Exception:
        return False
