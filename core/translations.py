# core/translations.py
"""
Traductions FR / EN / Lingala.
- Clé manquante : log_warning explicite (plus de retour de la clé brute silencieux)
- Variables manquantes : log_warning détaillé
"""

from core.utils.logs import log_warning

LANGUES_DISPONIBLES = {
    "fr": "Français",
    "en": "English",
    "ln": "Lingala",
}

TEXTES = {
    "fr": {
        "welcome": "ASSISTANT PRO\n\nBienvenue {nom} !\n\nStatut : {statut}\nPronostics : {compteur}/{limite}\n\nMatchs analysés : {nb_matchs}\nPrécision : {precision}%\n\nChoisis une option :",
        "fallback": "Je n'ai pas compris ta demande.\n\nUtilise les boutons du menu ci-dessous pour naviguer.",
        "banni": "🚫 Tu es banni de ce bot.",
        "aide": "📖 AIDE\n\nCommandes :\n/start : Menu principal\n/langue : Changer de langue\n/notif_on : Activer les notifications\n/notif_off : Désactiver les notifications\n/myid : Ton ID",
        "demande_affiche": "Tape l'affiche du match :\n\nEquipeDom vs EquipeExt\n\nExemples :\npsg vs marseille\nbarca vs real",
        "limite_atteinte": "⚠️ Limite atteinte ({limite}/jour).\n\nPasse en Premium pour des pronostics illimités !",
        "modele_chargement": "Chargement du modèle...",
        "modele_charge": "Modèle chargé !\n{nb_matchs} matchs | Précision : {precision}%",
        "erreur_equipe": "Erreur : {erreur}\n\nEssaie : psg vs marseille",
        "stats_ia": "📊 STATISTIQUES IA\n\nMatchs analysés : {nb_matchs}\nPrécision : {precision}%",
        "historique_vide": "📜 Aucun historique pour l'instant.\n\nFais ton premier pronostic avec ⚽ Faire un Pronostic !",
        "historique_titre": "📜 Tes 5 derniers pronostics\n\n",
        "premium_actif": "💎 Tu es déjà Premium !",
        "premium_titre": "💎 ABONNEMENT PREMIUM\n\nAvantages :\n• Pronostics illimités\n• Score exact + Over/BTTS\n• Support prioritaire\n\nFormules :\nJournalier : 2 000 CDF\nHebdomadaire : 6 000 CDF\nMensuel : 10 000 CDF",
        "premium_choix_titre": "💎 ABONNEMENT PREMIUM\n\nChoisis ton mode de paiement :",
        "btn_pay_stars": "Payer avec Telegram Stars",
        "btn_pay_mobile": "Payer par Mobile Money",
        "btn_pay_code": "J'ai un code Premium",
        "notifs_titre": "🔔 NOTIFICATIONS\n\nChaque matin à 8h, tu recevras les 3 meilleurs pronostics.\n\nChoisis une option :",
        "notifs_activees": "✅ Notifications ACTIVÉES",
        "notifs_desactivees": "❌ Notifications DÉSACTIVÉES",
        "bouton_activer": "Activer",
        "bouton_desactiver": "Désactiver",
        "choix_langue": "🌍 Choisis ta langue :",
        "langue_changee": "✅ Langue changée en Français",
        "parrainage_titre": "🤝 PARRAINAGE\n\nInvite tes amis et gagne des jours Premium gratuits !\n\nGains :\n- 1 ami inscrit = 1 jour Premium pour toi ET ton ami\n- 5 amis inscrits = 7 jours Premium bonus\n\nTon lien :\n{lien}\n\nTes stats :\n- Filleuls : {nb_filleuls}\n- Ton code : {code}",
        "parrainage_bienvenue": "Bienvenue ! Tu as été parrainé.\n\n+1 jour Premium pour toi et ton parrain !",
        "parrainage_bonus_5": "Félicitations ! Tu as atteint 5 filleuls.\n\n+7 jours Premium bonus !",
        "parrainage_classement_titre": "🏆 CLASSEMENT DES PARRAINS",
        "parrainage_mes_filleuls": "👥 MES FILLEULS",
        "parrainage_aucun_filleul": "Tu n'as pas encore de filleul.",
        "parrainage_palier_actuel": "🏆 Palier atteint : {nom} (bonus +{bonus}j)",
        "parrainage_prochain_palier": "🎯 Prochain palier : {nom} dans {restant} filleul(s) (+{bonus}j bonus)",
        "parrainage_bonus_palier": "Félicitations ! Tu as atteint le palier {nom}.\n\n+{bonus} jours Premium bonus !",
        "pay_mobile_titre": "📱 PAIEMENT MOBILE MONEY\n\nEnvoie le montant de {montant} CDF pour l'abonnement {abo} sur l'un de ces numéros :\n",
        "pay_code_titre": "🎟️ Tape ton code Premium :",
        "pay_code_ok": "✅ Code valide ! +{jours} jours Premium !",
        "pay_code_erreur": "❌ Erreur : {erreur}",
        "pay_attente_titre": "⏳ Demande envoyée !\n\nL'admin va vérifier ton paiement.\nTu recevras une notification après validation.",
        "pay_valide": "✅ Paiement validé ! +{jours} jours Premium !",
        "pay_refuse": "❌ Ton paiement a été refusé.\nContacte l'admin pour plus d'infos.",
        "titre_matchs_jour": "📅 MATCHS DU JOUR - {date}",
        "aucun_match_jour": "📅 Aucun match aujourd'hui ({date}).",
        "tip_matchs_jour": "Choisis '⚽ Faire un Pronostic' pour plus de détails.",
        "coupons_titre": "🎟️ COUPONS DU JOUR",
        "top_affiches_titre": "🏆 TOP AFFICHES DU JOUR",
        "aucun_coupon": "🎟️ Aucun coupon disponible aujourd'hui.",
        "aucune_affiche": "🏆 Aucune affiche à fort potentiel aujourd'hui.",
        "coupons_free_hint": "⭐ Passe Premium pour voir tous les coupons et les détails complets !",
        "btn_pronostic": "⚽ Faire un Pronostic",
        "btn_historique": "📜 Historique",
        "btn_stats": "📊 Statistiques",
        "btn_notifs": "🔔 Notifications",
        "btn_premium": "💎 Premium",
        "btn_langue": "🌍 Langue",
        "btn_matchs_jour": "📅 Matchs du Jour",
        "btn_parrainage": "🤝 Parrainage",
        "btn_coupons": "🎟️ Coupons",
        "btn_top_affiches": "🏆 Top Affiches",
    },
    "en": {
        "welcome": "PRO ASSISTANT\n\nWelcome {nom}!\n\nStatus: {statut}\nPredictions: {compteur}/{limite}\n\nMatches analyzed: {nb_matchs}\nAccuracy: {precision}%\n\nChoose an option:",
        "fallback": "I didn't understand.\n\nUse the menu buttons below.",
        "banni": "🚫 You are banned from this bot.",
        "aide": "📖 HELP\n\nCommands:\n/start: Main menu\n/langue: Change language\n/notif_on: Enable notifications\n/notif_off: Disable notifications\n/myid: Your ID",
        "demande_affiche": "Type the match:\n\nHomeTeam vs AwayTeam\n\nExamples:\npsg vs marseille\nbarca vs real",
        "limite_atteinte": "⚠️ Limit reached ({limite}/day).\n\nGo Premium for unlimited predictions!",
        "modele_chargement": "Loading model...",
        "modele_charge": "Model loaded!\n{nb_matchs} matches | Accuracy: {precision}%",
        "erreur_equipe": "Error: {erreur}\n\nTry: psg vs marseille",
        "stats_ia": "📊 AI STATISTICS\n\nMatches analyzed: {nb_matchs}\nAccuracy: {precision}%",
        "historique_vide": "📜 No history yet.",
        "historique_titre": "📜 Your last 5 predictions\n\n",
        "premium_actif": "💎 You are already Premium!",
        "premium_titre": "💎 PREMIUM SUBSCRIPTION\n\nBenefits:\n• Unlimited predictions\n• Exact score + Over/BTTS\n• Priority support\n\nPlans:\nDaily: 2,000 CDF\nWeekly: 6,000 CDF\nMonthly: 10,000 CDF",
        "premium_choix_titre": "💎 PREMIUM SUBSCRIPTION\n\nChoose your payment method:",
        "btn_pay_stars": "Pay with Telegram Stars",
        "btn_pay_mobile": "Pay with Mobile Money",
        "btn_pay_code": "I have a Premium code",
        "notifs_titre": "🔔 NOTIFICATIONS\n\nEvery morning at 8am, you'll receive the top 3 predictions.\n\nChoose an option:",
        "notifs_activees": "✅ Notifications ENABLED",
        "notifs_desactivees": "❌ Notifications DISABLED",
        "bouton_activer": "Enable",
        "bouton_desactiver": "Disable",
        "choix_langue": "🌍 Choose your language:",
        "langue_changee": "✅ Language changed to English",
        "parrainage_titre": "🤝 REFERRAL\n\nInvite your friends and earn free Premium days!\n\nRewards:\n- 1 friend = 1 Premium day for you AND your friend\n- 5 friends = 7 bonus Premium days\n\nYour link:\n{lien}\n\nYour stats:\n- Referrals: {nb_filleuls}\n- Your code: {code}",
        "parrainage_bienvenue": "Welcome! You were referred by a friend.\n\n+1 Premium day for you and your referrer!",
        "parrainage_bonus_5": "Congratulations! You reached 5 referrals.\n\n+7 bonus Premium days!",
        "parrainage_classement_titre": "🏆 TOP REFERRERS",
        "parrainage_mes_filleuls": "👥 MY REFERRALS",
        "parrainage_aucun_filleul": "You don't have any referral yet.",
        "parrainage_palier_actuel": "🏆 Reached tier: {nom} (bonus +{bonus}d)",
        "parrainage_prochain_palier": "🎯 Next tier: {nom} in {restant} referral(s) (+{bonus}d bonus)",
        "parrainage_bonus_palier": "Congratulations! You reached the {nom} tier.\n\n+{bonus} bonus Premium days!",
        "pay_mobile_titre": "📱 MOBILE MONEY PAYMENT\n\nSend {montant} CDF for the {abo} subscription to one of these numbers:\n",
        "pay_code_titre": "🎟️ Type your Premium code:",
        "pay_code_ok": "✅ Valid code! +{jours} Premium days!",
        "pay_code_erreur": "❌ Error: {erreur}",
        "pay_attente_titre": "⏳ Request sent!\n\nThe admin will verify your payment.\nYou will be notified upon validation.",
        "pay_valide": "✅ Payment validated! +{jours} Premium days!",
        "pay_refuse": "❌ Your payment was rejected.\nContact admin for more info.",
        "titre_matchs_jour": "📅 TODAY'S MATCHES - {date}",
        "aucun_match_jour": "📅 No match today ({date}).",
        "tip_matchs_jour": "Choose '⚽ Make a Prediction' for details.",
        "coupons_titre": "🎟️ TODAY'S COUPONS",
        "top_affiches_titre": "🏆 TODAY'S TOP MATCHES",
        "aucun_coupon": "🎟️ No coupon available today.",
        "aucune_affiche": "🏆 No high-potential match today.",
        "coupons_free_hint": "⭐ Go Premium to see all coupons and full details!",
        "btn_pronostic": "⚽ Make a Prediction",
        "btn_historique": "📜 History",
        "btn_stats": "📊 Statistics",
        "btn_notifs": "🔔 Notifications",
        "btn_premium": "💎 Premium",
        "btn_langue": "🌍 Language",
        "btn_matchs_jour": "📅 Today's Matches",
        "btn_parrainage": "🤝 Referral",
        "btn_coupons": "🎟️ Coupons",
        "btn_top_affiches": "🏆 Top Matches",
    },
    "ln": {
        "welcome": "MOSALISI PRO\n\nMbote {nom}!\n\nStatut: {statut}\nBakano: {compteur}/{limite}\n\nMasano: {nb_matchs}\nBosembo: {precision}%\n\nPona eloko:",
        "fallback": "Nazangi ntina.\n\nSalela ba boutons ya menu.",
        "banni": "🚫 Ozali banni na bot oyo.",
        "aide": "📖 LISUNGI\n\nBa commandes:\n/start: Menu\n/langue: Bongisa monoko\n/notif_on: Fungola nsango\n/notif_off: Kanga nsango\n/myid: ID na yo",
        "demande_affiche": "Koma lisano:\n\nHomeTeam vs AwayTeam\n\nNdakisa:\npsg vs marseille",
        "limite_atteinte": "⚠️ Soki ekokani ({limite}/mokolo).\n\nKende Premium mpo na bakano ekomi na ndelo te!",
        "modele_chargement": "Ezali kokotisa modele...",
        "modele_charge": "Modele ekomi!\n{nb_matchs} masano | Bosembo: {precision}%",
        "erreur_equipe": "Libunga: {erreur}\n\nMeka: psg vs marseille",
        "stats_ia": "📊 MITUYA YA IA\n\nMasano: {nb_matchs}\nBosembo: {precision}%",
        "historique_vide": "📜 Lisolo ezali te.",
        "historique_titre": "📜 Bakano na yo 5 ya suka\n\n",
        "premium_actif": "💎 Ozali deja Premium!",
        "premium_titre": "💎 ABONNEMENT PREMIUM\n\nBolamu:\n- Bakano ekomi na ndelo te\n- Score ya sembo\n- Lisungi ya liboso\n\nNtalo:\nMokolo: 2 000 CDF\nPɔsɔ: 6 000 CDF\nSanza: 10 000 CDF",
        "premium_choix_titre": "💎 ABONNEMENT PREMIUM\n\nPona ndenge ya kofuta :",
        "btn_pay_stars": "Futa na Telegram Stars",
        "btn_pay_mobile": "Futa na Mobile Money",
        "btn_pay_code": "Nazali na code Premium",
        "notifs_titre": "🔔 NSANGO\n\nMbula na mbula na 8h, okomona bakano 3 ya malamu.\n\nPona eloko:",
        "notifs_activees": "✅ Nsango EZALI",
        "notifs_desactivees": "❌ Nsango EZALI TE",
        "bouton_activer": "Fungola",
        "bouton_desactiver": "Kanga",
        "choix_langue": "🌍 Pona monoko na yo:",
        "langue_changee": "✅ Monoko ebongwani na Lingala",
        "parrainage_titre": "🤝 BOSANGISI\n\nBenga baninga na yo mpo na kozwa mikolo ya Premium ofele!\n\nBolamu :\n- 1 moninga = 1 mokolo Premium mpo na yo mpe moninga\n- 5 baninga = 7 mikolo Premium bonus\n\nLien na yo :\n{lien}\n\nStatistiques :\n- Ba filleuls : {nb_filleuls}\n- Code na yo : {code}",
        "parrainage_bienvenue": "Boyeyi malamu! Moninga moko abengaki yo.\n\n+1 mokolo Premium mpo na yo mpe mobengi!",
        "parrainage_bonus_5": "Matondo! Ozwi baninga 5.\n\n+7 mikolo Premium bonus!",
        "parrainage_classement_titre": "🏆 CLASSEMENT YA BA PARRAINS",
        "parrainage_mes_filleuls": "👥 BA FILLEULS NA NGAI",
        "parrainage_aucun_filleul": "Ozali na filleul moko te.",
        "parrainage_palier_actuel": "🏆 Palier : {nom} (bonus +{bonus}m)",
        "parrainage_prochain_palier": "🎯 Palier ya sima : {nom} na {restant} filleul(s) (+{bonus}m)",
        "parrainage_bonus_palier": "Matondo! Ozwi palier {nom}.\n\n+{bonus} mikolo Premium!",
        "pay_mobile_titre": "📱 KOFUTA NA MOBILE MONEY\n\nTinda {montant} CDF mpo na abonnement {abo} na moko ya ba nimero oyo :\n",
        "pay_code_titre": "🎟️ Koma code Premium na yo :",
        "pay_code_ok": "✅ Code ezali malamu! +{jours} mikolo Premium!",
        "pay_code_erreur": "❌ Libunga : {erreur}",
        "pay_attente_titre": "⏳ Demande etindami!\n\nAdmin akotalela paiement na yo.\nOkoyoka tango eko valider.",
        "pay_valide": "✅ Paiement evalidé! +{jours} mikolo Premium!",
        "pay_refuse": "❌ Paiement na yo ebotami te.\nBenga admin mpo na makambo mosusu.",
        "titre_matchs_jour": "📅 MASANO YA LELO - {date}",
        "aucun_match_jour": "📅 Masano ezali te lelo ({date}).",
        "tip_matchs_jour": "Pona '⚽ Sala Bokano' mpo na makambo mosusu.",
        "coupons_titre": "🎟️ BA COUPONS YA LELO",
        "top_affiches_titre": "🏆 AFFICHES YA MALAMU YA LELO",
        "aucun_coupon": "🎟️ Coupon moko te lelo.",
        "aucune_affiche": "🏆 Affiche ya malamu moko te lelo.",
        "coupons_free_hint": "⭐ Kende Premium mpo na komona ba coupons nyonso!",
        "btn_pronostic": "⚽ Sala Bokano",
        "btn_historique": "📜 Lisolo",
        "btn_stats": "📊 Mituya",
        "btn_notifs": "🔔 Nsango",
        "btn_premium": "💎 Premium",
        "btn_langue": "🌍 Monoko",
        "btn_matchs_jour": "📅 Masano ya lelo",
        "btn_parrainage": "🤝 Bosangisi",
        "btn_coupons": "🎟️ Ba coupons",
        "btn_top_affiches": "🏆 Affiches ya malamu",
    },
}


def get_text(cle, langue="fr", **kwargs):
    """
    Retourne le texte traduit.
    - Si la clé n'existe pas : log_warning + fallback FR + retour de la clé
    - Si une variable manque : log_warning + retour du texte brut
    """
    if langue not in TEXTES:
        langue = "fr"

    texte = TEXTES[langue].get(cle)
    if texte is None:
        texte_fr = TEXTES["fr"].get(cle)
        if texte_fr is None:
            log_warning(
                message=f"Clé de traduction introuvable dans TOUTES les langues : '{cle}'",
                module="TRANSLATIONS",
                extra={"cle": cle, "langue_demandee": langue},
            )
            return cle
        log_warning(
            message=f"Clé '{cle}' absente en '{langue}', fallback FR",
            module="TRANSLATIONS",
            extra={"cle": cle, "langue": langue},
        )
        texte = texte_fr

    if kwargs:
        try:
            return texte.format(**kwargs)
        except KeyError as e:
            log_warning(
                message=f"Variable '{e}' manquante pour la clé '{cle}' (langue={langue})",
                module="TRANSLATIONS",
                extra={"cle": cle, "langue": langue, "manquante": str(e)},
            )
            return texte
        except Exception as e:
            log_warning(
                message=f"Erreur de formatage de '{cle}' (langue={langue})",
                module="TRANSLATIONS",
                extra={"cle": cle, "langue": langue},
                exception=e,
            )
            return texte

    return texte
