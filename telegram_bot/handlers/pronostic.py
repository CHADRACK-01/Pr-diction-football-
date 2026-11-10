import telebot

from users import get_langue, est_banni, peut_faire_pronostic, get_limite_jour, est_administrateur
from core.translations import get_text
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS
from core.session import set_session_competition, clear_session_competition
from users.matchs import get_equipes_saison_en_cours
from core.utils.logs import log_info, log_error, log_warning


def _creer_clavier_principal(user_id):
    """Recrée le clavier principal (après un pronostic ou un retour)."""
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
    except Exception as e:
        log_warning(f"Impossible de vérifier le statut admin pour {user_id} : {e}", "PRONOSTIC")
    return markup


def _creer_clavier_competitions():
    """Crée le clavier des compétitions."""
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
    """Crée un clavier avec les équipes (3 par ligne)."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    boutons = [telebot.types.KeyboardButton(eq) for eq in equipes]
    markup.add(*boutons)
    markup.add(telebot.types.KeyboardButton("↩️ Retour au Menu"))
    return markup


def afficher_menu_competitions(bot, message):
    """Affiche le menu des compétitions."""
    user_id = message.from_user.id
    
    try:
        langue = get_langue(user_id)
    except Exception as e:
        log_error(f"Impossible de récupérer la langue de {user_id}", "PRONOSTIC", exception=e)
        langue = "fr"

    try:
        if est_banni(user_id):
            bot.reply_to(message, get_text("banni", langue))
            return
    except Exception as e:
        log_error(f"Impossible de vérifier si {user_id} est banni", "PRONOSTIC", exception=e)
        return

    try:
        if not peut_faire_pronostic(user_id):
            limite = get_limite_jour(user_id)
            bot.reply_to(message, get_text("limite_atteinte", langue, limite=limite))
            return
    except Exception as e:
        log_error(f"Impossible de vérifier la limite de {user_id}", "PRONOSTIC", exception=e)
        bot.reply_to(message, "❌ Erreur lors de la vérification de tes limites.")
        return

    markup = _creer_clavier_competitions()
    bot.reply_to(message, "⚽ **Choisis la compétition** :", reply_markup=markup, parse_mode="Markdown")


def enregistrer_pronostic_handlers(bot):
    """Enregistre les handlers pour le flux de pronostic."""

    @bot.message_handler(func=lambda m: m.text == "⚽ Faire un Pronostic")
    def handle_pronostic(message):
        afficher_menu_competitions(bot, message)

    @bot.message_handler(func=lambda m: m.text == "↩️ Retour au Menu")
    def retour_menu(message):
        user_id = message.from_user.id
        try:
            clear_session_competition(user_id)
        except Exception as e:
            log_error(f"Impossible de supprimer la session de {user_id}", "PRONOSTIC", exception=e)
        from telegram_bot.handlers.start import envoyer_menu_principal
        envoyer_menu_principal(message.chat.id, user_id, bot)

    @bot.message_handler(func=lambda m: m.text and any(nom in m.text for nom in CHAMPIONNATS.values()))
    def handle_choix_competition(message):
        """Étape 1 : l'utilisateur a choisi une compétition."""
        user_id = message.from_user.id
        texte_bouton = message.text

        # Détection de la compétition choisie
        comp_code, nom_propre = None, None
        for code, nom in CHAMPIONNATS.items():
            if nom in texte_bouton:
                comp_code = code
                nom_propre = nom
                break

        if not comp_code:
            return

        log_info(f"Compétition choisie par {user_id} : {nom_propre}", "PRONOSTIC")

        # Sauvegarde de la compétition en session
        try:
            set_session_competition(user_id, comp_code)
        except Exception as e:
            log_error(f"Impossible de sauvegarder la compétition {comp_code} pour {user_id}", "PRONOSTIC", exception=e)
            bot.reply_to(message, "❌ Impossible de sauvegarder ta compétition. Réessaie.")
            return

        # Récupération des équipes de la saison en cours
        try:
            equipes = get_equipes_saison_en_cours(nom_propre)
        except Exception as e:
            log_error(f"Impossible de récupérer les équipes de {nom_propre}", "PRONOSTIC", exception=e)
            bot.reply_to(message, "❌ Erreur lors de la récupération des équipes. L'admin a été prévenu.")
            return
        
        if not equipes:
            bot.reply_to(message, f"⚠️ Aucune équipe trouvée pour **{nom_propre}** cette saison.", parse_mode="Markdown")
            return

        # Affichage du clavier des équipes
        markup = _creer_clavier_equipes(equipes)
        
        # Stockage de la session en mémoire
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        ADMIN_SESSIONS[user_id] = {
            "action": "prono_domicile",
            "competition": comp_code,
            "nom_competition": nom_propre,
            "equipes": equipes
        }

        bot.send_message(
            message.chat.id,
            f"⚽ Compétition choisie : **{nom_propre}**\n\n🏠 Sélectionne l'équipe **à domicile** :",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda m: m.text and _est_en_session_domicile(m.from_user.id))
    def handle_choix_domicile(message):
        """Étape 2 : l'utilisateur a choisi l'équipe à domicile."""
        user_id = message.from_user.id
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        
        session = ADMIN_SESSIONS.get(user_id, {})
        equipes = session.get("equipes", [])
        
        equipe_dom = message.text.strip()
        
        # Vérification que l'équipe est bien dans la liste
        if equipe_dom not in equipes:
            return
        
        log_info(f"Équipe domicile choisie par {user_id} : {equipe_dom}", "PRONOSTIC")
        
        # Passage à l'étape 2
        session["action"] = "prono_exterieur"
        session["equipe_dom"] = equipe_dom
        ADMIN_SESSIONS[user_id] = session
        
        # On propose les équipes extérieures (toutes sauf celle à domicile)
        equipes_ext = [eq for eq in equipes if eq != equipe_dom]
        markup = _creer_clavier_equipes(equipes_ext)
        
        bot.send_message(
            message.chat.id,
            f"🏠 Domicile : **{equipe_dom}**\n\n✈️ Sélectionne maintenant l'équipe **à l'extérieur** :",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda m: m.text and _est_en_session_exterieur(m.from_user.id))
    def handle_choix_exterieur(message):
        """Étape 3 : l'utilisateur a choisi l'équipe à l'extérieur. On fait la prédiction."""
        user_id = message.from_user.id
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        
        session = ADMIN_SESSIONS.get(user_id, {})
        equipes = session.get("equipes", [])
        
        equipe_ext = message.text.strip()
        
        # Vérification que l'équipe est bien dans la liste
        if equipe_ext not in equipes:
            return
        
        equipe_dom = session.get("equipe_dom", "")
        comp_code = session.get("competition", "")
        
        log_info(f"Équipe extérieur choisie par {user_id} : {equipe_ext}. Lancement de la prédiction...", "PRONOSTIC")
        
        # On nettoie la session
        ADMIN_SESSIONS.pop(user_id, None)
        
        # On remet le clavier principal
        markup = _creer_clavier_principal(user_id)
        
        try:
            from core.prediction import predire_match, sauvegarder_historique
            from users import est_premium, incrementer_compteur
            
            clear_session_competition(user_id)
            
            competition_reelle = MAPPING_COMPETITIONS.get(comp_code, comp_code)
            
            bot.send_message(
                message.chat.id,
                f"⏳ Calcul de la prédiction pour **{equipe_dom} vs {equipe_ext}**...",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
            resultat = predire_match(equipe_dom, equipe_ext, competition=competition_reelle)
            
            if "erreur" in resultat:
                erreur_msg = resultat["erreur"]
                if "Données insuffisantes" in erreur_msg or "non supportée" in erreur_msg:
                    bot.send_message(message.chat.id, erreur_msg)
                else:
                    log_error(f"Erreur de prédiction pour {equipe_dom} vs {equipe_ext} : {erreur_msg}", "PRONOSTIC")
                    bot.send_message(message.chat.id, f"❌ {erreur_msg}")
                return
            
            # Affichage du bulletin
            from telegram_bot.prediction_handlers import _formater_bulletin_premium, _formater_bulletin_free
            is_prem = est_premium(user_id)
            bulletin = _formater_bulletin_premium(resultat) if is_prem else _formater_bulletin_free(resultat)
            
            bot.send_message(message.chat.id, bulletin, parse_mode='Markdown')
            
            # Sauvegarde de l'historique
            try:
                sauvegarder_historique(
                    resultat['home_team'], resultat['away_team'],
                    resultat['p_h'], resultat['p_d'], resultat['p_a'],
                    resultat['best_score'][0], resultat['best_score'][1]
                )
            except Exception as e:
                log_error(f"Impossible de sauvegarder l'historique pour {user_id}", "PRONOSTIC", exception=e)
            
            # Incrémentation du compteur
            try:
                incrementer_compteur(user_id)
            except Exception as e:
                log_error(f"Impossible d'incrémenter le compteur de {user_id}", "PRONOSTIC", exception=e)
            
        except Exception as e:
            log_error(f"Impossible de calculer la prédiction pour {user_id}", "PRONOSTIC", exception=e)
            bot.send_message(message.chat.id, "❌ Erreur lors de la prédiction. L'admin a été prévenu.")


def _est_en_session_domicile(user_id):
    """Vérifie si l'utilisateur est en attente de choix de l'équipe à domicile."""
    try:
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        return ADMIN_SESSIONS.get(user_id, {}).get("action") == "prono_domicile"
    except Exception:
        return False


def _est_en_session_exterieur(user_id):
    """Vérifie si l'utilisateur est en attente de choix de l'équipe à l'extérieur."""
    try:
        from telegram_bot.admin.actions import ADMIN_SESSIONS
        return ADMIN_SESSIONS.get(user_id, {}).get("action") == "prono_exterieur"
    except Exception:
        return False
