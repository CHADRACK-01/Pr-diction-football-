"""Commandes Telegram des fonctionnalités locales complétées."""

from core.analyses_avancees import (
    simuler_monte_carlo,
    calculer_elo_live,
    detecter_derby,
    calculer_fatigue_calendrier,
)
from core.gestion_risques import evaluer_plan_anti_perte, evaluer_cashout_partiel
from core.engagement_local import obtenir_engagement, bonus_connexion_quotidienne, tourner_roue


def enregistrer_completions_handlers(bot):

    @bot.message_handler(commands=["daily"])
    def cmd_daily(message):
        date_jour = message.date.strftime("%Y-%m-%d") if getattr(message, "date", None) else ""
        if not date_jour:
            from datetime import datetime
            date_jour = datetime.now().strftime("%Y-%m-%d")
        resultat = bonus_connexion_quotidienne(message.from_user.id, date_jour)
        if resultat["attribue"]:
            texte = f"🎁 <b>Bonus quotidien</b>\n+{resultat['xp']} XP — série : {resultat['serie']} jour(s)"
        else:
            texte = "📅 Bonus déjà récupéré aujourd'hui."
        bot.reply_to(message, texte, parse_mode="HTML")

    @bot.message_handler(commands=["roue"])
    def cmd_roue(message):
        from datetime import datetime
        date_jour = datetime.now().strftime("%Y-%m-%d")
        resultat = tourner_roue(message.from_user.id, date_jour)
        if not resultat["attribue"]:
            texte = "🎡 Tu as déjà utilisé ta roue aujourd'hui."
        else:
            texte = f"🎡 <b>Résultat :</b> {resultat['gain']}"
        bot.reply_to(message, texte, parse_mode="HTML")

    @bot.message_handler(commands=["xp"])
    def cmd_xp(message):
        engagement = obtenir_engagement(message.from_user.id)
        bot.reply_to(message, f"⭐ <b>Ton solde XP</b> : {engagement['xp']}", parse_mode="HTML")

    @bot.message_handler(commands=["montecarlo"])
    def cmd_monte_carlo(message):
        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(message, "Usage : <code>/montecarlo 1.5 1.2 10000</code>", parse_mode="HTML")
            return
        try:
            lambda_home, lambda_away = float(args[1]), float(args[2])
            simulations = max(100, min(int(args[3]), 100000))
            resultat = simuler_monte_carlo(lambda_home, lambda_away, simulations, graine=42)
            probabilites = resultat["probabilites"]
            texte = (
                "🎲 <b>SIMULATION MONTE CARLO</b>\n"
                f"{simulations:,} simulations\n"
                f"🏠 Victoire domicile : {probabilites['1']:.1%}\n"
                f"⚖️ Match nul : {probabilites['N']:.1%}\n"
                f"✈️ Victoire extérieur : {probabilites['2']:.1%}"
            )
            bot.reply_to(message, texte, parse_mode="HTML")
        except (ValueError, TypeError):
            bot.reply_to(message, "❌ Paramètres invalides.")

    @bot.message_handler(commands=["derby"])
    def cmd_derby(message):
        args = message.text.split(" vs ", maxsplit=1)
        if len(args) != 2:
            bot.reply_to(message, "Usage : <code>/derby Equipe1 vs Equipe2</code>", parse_mode="HTML")
            return
        home, away = args[0].replace("/derby", "", 1).strip(), args[1].strip()
        texte = "🔴 <b>DERBY / RIVALITÉ</b>" if detecter_derby(home, away) else "✅ <b>Match standard</b>"
        bot.reply_to(message, texte, parse_mode="HTML")

    @bot.message_handler(commands=["elo"])
    def cmd_elo(message):
        args = message.text.split()
        if len(args) != 6:
            bot.reply_to(message, "Usage : <code>/elo 1500 1500 1 0 home</code>", parse_mode="HTML")
            return
        try:
            elo_home, elo_away = float(args[1]), float(args[2])
            score = (int(args[3]), int(args[4]))
            but_equipe = args[5].lower()
            if but_equipe not in {"home", "away"}:
                raise ValueError
            resultat = calculer_elo_live(
                elo_home,
                elo_away,
                score_actuel=score,
                but_equipe=but_equipe,
            )
            bot.reply_to(message, f"📈 Elo — Domicile : {resultat['home']} | Extérieur : {resultat['away']}")
        except (ValueError, IndexError):
            bot.reply_to(message, "❌ Paramètres Elo invalides.")

    @bot.message_handler(commands=["fatigue"])
    def cmd_fatigue(message):
        args = message.text.split()[1:]
        if not args:
            bot.reply_to(message, "Usage : <code>/fatigue 2026-11-18 2026-11-21 2026-11-24</code>", parse_mode="HTML")
            return
        resultat = calculer_fatigue_calendrier(args)
        niveau = "ÉLEVÉE" if resultat["alerte"] else "NORMAL"
        bot.reply_to(message, f"📅 <b>Fatigue calendrier :</b> {niveau} ({resultat['epuisement']}/10)", parse_mode="HTML")

    @bot.message_handler(commands=["antiperte"])
    def cmd_antiperte(message):
        resultats = message.text.split()[1:]
        resultat = evaluer_plan_anti_perte(resultats)
        statut = "ACTIF — seuls les paris sécurisés sont proposés" if resultat["active"] else "Normal"
        bot.reply_to(message, f"🛡️ <b>Plan anti-perte :</b> {statut}", parse_mode="HTML")

    @bot.message_handler(commands=["cashpartiel"])
    def cmd_cashpartiel(message):
        args = message.text.split()
        if len(args) != 5:
            bot.reply_to(message, "Usage : <code>/cashpartiel MISE COTE_INIT COTE_ACTUELLE 0.5</code>", parse_mode="HTML")
            return
        try:
            mise, initiale, actuelle, fraction = map(float, args[1:])
            resultat = evaluer_cashout_partiel(mise, initiale, actuelle, fraction)
            bot.reply_to(
                message,
                "💸 <b>Cash-out partiel</b>\n"
                f"Encaisser : {resultat['encaisse_immediate']:,.2f}\n"
                f"Laisser courir : {resultat['reste_enjeu']:,.2f}",
                parse_mode="HTML",
            )
        except (ValueError, TypeError):
            bot.reply_to(message, "❌ Paramètres invalides.")

    @bot.message_handler(commands=["catalogue"])
    def cmd_catalogue(message):
        bot.reply_to(message, "📚 <b>Catalogue des fonctionnalités</b> :", parse_mode="HTML", reply_markup=creer_menu_catalogue())

    @bot.callback_query_handler(func=lambda call: call.data in {"catmenu"} or call.data.startswith(("cat|", "grp|", "fic|")))
    def handle_catalogue_callbacks(call):
        from core.catalogue_fonctionnalites import obtenir_catalogue

        catalogue = obtenir_catalogue()
        data = call.data

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if data == "catmenu":
            bot.edit_message_text(
                "🗂️ <b>CATALOGUE COMPLET DES FONCTIONNALITÉS</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=creer_menu_catalogue(),
                parse_mode="HTML",
            )
            return

        if data.startswith("cat|"):
            prefix = data.split("|", 1)[1]
            groupe = next((g for g in {item["groupe"] for item in catalogue.values()} if g.startswith(prefix)), prefix)
            bot.edit_message_text(
                f"🗂️ <b>{groupe}</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=creer_menu_groupe(groupe),
                parse_mode="HTML",
            )
            return

        if data.startswith("grp|"):
            _, prefix, page = data.split("|", 2)
            groupe = next((g for g in {item["groupe"] for item in catalogue.values()} if g.startswith(prefix)), prefix)
            bot.edit_message_text(
                f"🗂️ <b>{groupe}</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=creer_menu_groupe(groupe, page=int(page)),
                parse_mode="HTML",
            )
            return

        if data.startswith("fic|"):
            feature_id = data.split("|", 1)[1]
            item = catalogue.get(feature_id)
            if not item:
                return
            statuts = {"complete": "✅ Implémentée", "partielle": "🟡 Partielle", "a_implanter": "🔴 À compléter"}
            texte = (
                f"<b>{feature_id}. {item['nom']}</b>\n"
                f"Groupe : {item['groupe']}\n"
                f"Statut : {statuts.get(item['statut'], '❔ Inconnu')}"
            )
            bot.edit_message_text(
                texte,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=creer_menu_catalogue(),
                parse_mode="HTML",
            )

    @bot.message_handler(commands=["ab"])
    def cmd_ab(message):
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage : <code>/ab USER_ID</code>", parse_mode="HTML")
            return
        try:
            from core.fonctionnalites_700 import test_ab
            variante = test_ab(int(args[1]))
            bot.reply_to(message, f"🧪 <b>Variante A/B</b> : {variante}", parse_mode="HTML")
        except (ValueError, TypeError):
            bot.reply_to(message, "❌ Identifiant utilisateur invalide.")

    @bot.message_handler(commands=["calibration"])
    def cmd_calibration(message):
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "Usage : <code>/calibration 0.7 1 0.2 0</code>", parse_mode="HTML")
            return
        try:
            from core.fonctionnalites_700 import score_brier, log_loss
            valeurs = list(map(float, args[1:]))
            if len(valeurs) % 2:
                raise ValueError
            probabilites = valeurs[0::2]
            resultats = valeurs[1::2]
            if any(p < 0 or p > 1 for p in probabilites):
                raise ValueError
            bot.reply_to(
                message,
                f"📏 <b>Calibration</b>\nBrier : {score_brier(probabilites, resultats)}\nLog-loss : {log_loss(probabilites, resultats)}",
                parse_mode="HTML",
            )
        except (ValueError, TypeError):
            bot.reply_to(message, "❌ Format : p1 r1 p2 r2 …")

    @bot.message_handler(commands=["runtime700"])
    def cmd_runtime700(message):
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage : <code>/runtime700 31</code>", parse_mode="HTML")
            return
        try:
            from core.runtime_700 import executer_fonctionnalite
            feature_id = int(args[1])
            resultat = executer_fonctionnalite(feature_id)
            if resultat["etat"] == "invalide":
                bot.reply_to(message, "❌ Identifiant de fonctionnalité inconnu.")
                return
            bot.reply_to(
                message,
                f"🧩 <b>Fonction {feature_id}</b>\n"
                f"Nom : {resultat.get('nom', 'Inconnu')}\n"
                f"Statut catalogue : {resultat.get('statut', 'inconnu')}\n"
                f"État runtime : {resultat.get('etat')}\n"
                f"{resultat.get('message', '')}",
                parse_mode="HTML",
            )
        except (TypeError, ValueError):
            bot.reply_to(message, "❌ Identifiant invalide.")


def creer_menu_catalogue():
    import telebot
    from core.catalogue_fonctionnalites import obtenir_catalogue

    catalogue = obtenir_catalogue()
    groupes = {}
    for feature_id, item in catalogue.items():
        groupes.setdefault(item["groupe"], []).append((feature_id, item))

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for groupe in sorted(groupes):
        markup.add(telebot.types.InlineKeyboardButton(
            f"{groupe} ({len(groupes[groupe])})",
            callback_data=f"cat|{groupe[:20]}",
        ))
    return markup


def creer_menu_groupe(groupe_recherche, page=0, taille_page=10):
    import telebot
    from core.catalogue_fonctionnalites import obtenir_catalogue

    catalogue = obtenir_catalogue()
    elements = [
        (feature_id, item)
        for feature_id, item in catalogue.items()
        if item["groupe"] == groupe_recherche
    ]
    debut = page * taille_page
    sous_liste = elements[debut:debut + taille_page]

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    statuts = {"complete": "✅", "partielle": "🟡", "a_implanter": "🔴"}
    for feature_id, item in sous_liste:
        marqueur = statuts.get(item["statut"], "❔")
        markup.add(telebot.types.InlineKeyboardButton(
            f"{marqueur} {feature_id}. {item['nom'][:45]}",
            callback_data=f"fic|{feature_id}",
        ))

    navigation = []
    if page > 0:
        navigation.append(telebot.types.InlineKeyboardButton("⬅️ Précédent", callback_data=f"grp|{groupe_recherche[:20]}|{page - 1}"))
    if debut + taille_page < len(elements):
        navigation.append(telebot.types.InlineKeyboardButton("➡️ Suivant", callback_data=f"grp|{groupe_recherche[:20]}|{page + 1}"))
    if navigation:
        markup.row(*navigation)
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Toutes les catégories", callback_data="catmenu"))
    return markup
