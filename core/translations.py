# =========================================================
# TRADUCTIONS MULTI-LANGUE
# =========================================================

LANGUES_DISPONIBLES = {
    "fr": "Français",
    "en": "English",
    "ln": "Lingala",
}

TEXTES = {
    "fr": {
        "welcome": "ASSISTANT PRO\n\nBienvenue {nom} !\n\nStatut : {statut}\nPronostics : {compteur}/{limite}\n\nMatchs analyses : {nb_matchs}\nPrecision : {precision}%\n\nChoisis une option :",
        "btn_pronostic": "Faire un Pronostic",
        "btn_historique": "Historique",
        "btn_stats": "Statistiques",
        "btn_notifs": "Notifications",
        "btn_premium": "Passer Premium",
        "btn_langue": "Langue",
        "choix_langue": "Choisis ta langue :",
        "langue_changee": "Langue changee en Français",
        "demande_affiche": "Tape l'affiche du match :\n\nEquipeDom vs EquipeExt\n\nExemples :\npsg vs marseille\nbarca vs real",
        "limite_atteinte": "Limite atteinte ({limite}/jour).\n\nPasse en Premium pour des pronostics illimites !",
        "modele_chargement": "Chargement du modele...",
        "modele_charge": "Modele charge !\n{nb_matchs} matchs | Precision : {precision}%",
        "stats_ia": "Statistiques IA\n\nMatchs analyses : {nb_matchs}\nPrecision : {precision}%",
        "historique_vide": "Aucun historique pour l'instant.",
        "historique_titre": "Tes 5 derniers pronostics\n\n",
        "premium_actif": "Tu es deja Premium !",
        "premium_titre": "Abonnement Premium\n\nAvantages :\n- Pronostics illimites\n- Score exact + Over/BTTS\n- Support prioritaire\n\nFormules :\nJournalier : 2 000 CDF\nHebdomadaire : 6 000 CDF\nMensuel : 10 000 CDF\n\nPaiement : Mobile Money (bientot disponible)",
        "notifs_titre": "Notifications\n\nChaque matin a 8h, tu recevras les 3 meilleurs pronostics.\n\nChoisis une option :",
        "notifs_activees": "Notifications ACTIVEES",
        "notifs_desactivees": "Notifications DESACTIVEES",
        "bouton_activer": "Activer",
        "bouton_desactiver": "Desactiver",
        "erreur_equipe": "Erreur : {erreur}\n\nEssaie : psg vs marseille",
        "fallback": "Utilise les boutons du menu.\n\nOu tape : Equipe A vs Equipe B",
        "banni": "Tu es banni de ce bot.",
        "aide": "Aide\n\nCommandes :\n/start : Menu principal\n/myid : Ton ID\n/notif_on : Activer les notifs\n/notif_off : Desactiver les notifs\n/langue : Changer de langue",
    },
    "en": {
        "welcome": "PRO ASSISTANT\n\nWelcome {nom}!\n\nStatus: {statut}\nPredictions: {compteur}/{limite}\n\nMatches analyzed: {nb_matchs}\nAccuracy: {precision}%\n\nChoose an option:",
        "btn_pronostic": "Make a Prediction",
        "btn_historique": "History",
        "btn_stats": "Statistics",
        "btn_notifs": "Notifications",
        "btn_premium": "Go Premium",
        "btn_langue": "Language",
        "choix_langue": "Choose your language:",
        "langue_changee": "Language changed to English",
        "demande_affiche": "Type the match:\n\nHomeTeam vs AwayTeam\n\nExamples:\npsg vs marseille\nbarca vs real",
        "limite_atteinte": "Limit reached ({limite}/day).\n\nGo Premium for unlimited predictions!",
        "modele_chargement": "Loading model...",
        "modele_charge": "Model loaded!\n{nb_matchs} matches | Accuracy: {precision}%",
        "stats_ia": "AI Statistics\n\nMatches analyzed: {nb_matchs}\nAccuracy: {precision}%",
        "historique_vide": "No history yet.",
        "historique_titre": "Your last 5 predictions\n\n",
        "premium_actif": "You are already Premium!",
        "premium_titre": "Premium Subscription\n\nBenefits:\n- Unlimited predictions\n- Exact score + Over/BTTS\n- Priority support\n\nPlans:\nDaily: 2,000 CDF\nWeekly: 6,000 CDF\nMonthly: 10,000 CDF\n\nPayment: Mobile Money (coming soon)",
        "notifs_titre": "Notifications\n\nEvery morning at 8am, you'll receive the top 3 predictions.\n\nChoose an option:",
        "notifs_activees": "Notifications ENABLED",
        "notifs_desactivees": "Notifications DISABLED",
        "bouton_activer": "Enable",
        "bouton_desactiver": "Disable",
        "erreur_equipe": "Error: {erreur}\n\nTry: psg vs marseille",
        "fallback": "Use the menu buttons.\n\nOr type: Team A vs Team B",
        "banni": "You are banned from this bot.",
        "aide": "Help\n\nCommands:\n/start: Main menu\n/myid: Your ID\n/notif_on: Enable notifications\n/notif_off: Disable notifications\n/langue: Change language",
    },
    "ln": {
        "welcome": "MOSALISI PRO\n\nMbote {nom}!\n\nStatut: {statut}\nBakano: {compteur}/{limite}\n\nMasano: {nb_matchs}\nBosembo: {precision}%\n\nPona eloko:",
        "btn_pronostic": "Sala Bokano",
        "btn_historique": "Lisolo",
        "btn_stats": "Mituya",
        "btn_notifs": "Nsango",
        "btn_premium": "Kende Premium",
        "btn_langue": "Monoko",
        "choix_langue": "Pona monoko na yo:",
        "langue_changee": "Monoko ebongwani na Lingala",
        "demande_affiche": "Koma lisano:\n\nHomeTeam vs AwayTeam\n\nNdakisa:\npsg vs marseille",
        "limite_atteinte": "Soki ekokani ({limite}/mokolo).\n\nKende Premium mpo na bakano ekomi na ndelo te!",
        "modele_chargement": "Ezali kokotisa modele...",
        "modele_charge": "Modele ekomi!\n{nb_matchs} masano | Bosembo: {precision}%",
        "stats_ia": "Mituya ya IA\n\nMasano: {nb_matchs}\nBosembo: {precision}%",
        "historique_vide": "Lisolo ezali te.",
        "historique_titre": "Bakano na yo 5 ya suka\n\n",
        "premium_actif": "Ozali deja Premium!",
        "premium_titre": "Abonnement Premium\n\nBolamu:\n- Bakano ekomi na ndelo te\n- Score ya sembo\n- Lisungi ya liboso\n\nNtalo:\nMokolo: 2 000 CDF\nPɔsɔ: 6 000 CDF\nSanza: 10 000 CDF\n\nMbongo: Mobile Money",
        "notifs_titre": "Nsango\n\nMbula na mbula na 8h, okomona bakano 3 ya malamu.\n\nPona eloko:",
        "notifs_activees": "Nsango EZALI",
        "notifs_desactivees": "Nsango EZALI TE",
        "bouton_activer": "Fungola",
        "bouton_desactiver": "Kanga",
        "erreur_equipe": "Libunga: {erreur}\n\nMeka: psg vs marseille",
        "fallback": "Salela ba boutons ya menu.\n\nTo koma: Ekip A vs Ekip B",
        "banni": "Ozali banni na bot oyo.",
        "aide": "Lisungi\n\nBa commandes:\n/start: Menu\n/myid: ID na yo\n/notif_on: Fungola nsango\n/notif_off: Kanga nsango\n/langue: Bongisa monoko",
    },
}


def get_text(cle, langue="fr", **kwargs):
    """Retourne le texte traduit avec les variables remplacées."""
    if langue not in TEXTES:
        langue = "fr"

    texte = TEXTES[langue].get(cle, TEXTES["fr"].get(cle, cle))

    if kwargs:
        try:
            texte = texte.format(**kwargs)
        except Exception:
            pass

    return texte
