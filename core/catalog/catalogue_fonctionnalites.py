"""Catalogue central des fonctionnalités annoncées par le projet, jusqu’à 700.

Ce module sert de source unique pour les identifiants, noms, groupes et
statuts d'implémentation afin d'éviter les divergences entre README, admin
et tests.
"""

FEATURES = (
    ("1", "Alertes Live / But en direct", "Live", "partielle"),
    ("2", "Détecteur de Value Bet", "Paris", "complete"),
    ("3", "Tracker de Chute de Cotes", "Paris", "complete"),
    ("4", "Alerte Compo Officielle / Absents", "Données", "a_implanter"),
    ("5", "Simulateur de Cash-Out", "Paris", "complete"),
    ("6", "Mode Lingala + Français", "Expérience", "complete"),
    ("7", "Historique Vérifiable Public", "Prédiction", "partielle"),
    ("8", "Filtre Anti-Piège", "Paris", "a_implanter"),
    ("9", "Prono Spécial Corners / Cartons", "Prédiction", "partielle"),
    ("10", "Calendrier Perso Mes Équipes", "Utilisateur", "complete"),
    ("11", "Ticket de la Semaine en PDF", "Contenu", "a_implanter"),
    ("12", "Quiz / Sondage Avant Match", "Engagement", "a_implanter"),
    ("13", "Mode Sans Internet / SMS Résumé", "Expérience", "a_implanter"),
    ("14", "Comparateur de Bookmakers RDC", "Paris", "complete"),
    ("15", "Analyse Vidéo Courte Auto", "Contenu", "a_implanter"),
    ("16", "Avertissement Jeu Responsable", "Sécurité", "partielle"),
    ("17", "Groupe VIP Auto-Modéré", "Paiement", "partielle"),
    ("18", "Prono Championnats Africains", "Données", "a_implanter"),
    ("19", "Copier le Ticket en 1 Clic", "Paris", "a_implanter"),
    ("20", "Statistiques de l'IA en Temps Réel", "Prédiction", "complete"),
    ("21", "Coach IA en Chat Libre", "Prédiction", "a_implanter"),
    ("22", "Détecteur de Série / Momentum", "Données", "complete"),
    ("23", "Spécialiste Match Nul", "Paris", "complete"),
    ("24", "Alerte But Tardif", "Live", "a_implanter"),
    ("25", "Stats Arbitre", "Données", "a_implanter"),
    ("26", "Modèle xG", "Prédiction", "partielle"),
    ("27", "Impact Transfert / Entraîneur", "Données", "a_implanter"),
    ("28", "Comparateur Domicile / Extérieur", "Données", "complete"),
    ("29", "Prono Buteur + Passeur", "Prédiction", "a_implanter"),
    ("30", "Mini App Telegram Visuelle", "Expérience", "a_implanter"),
    ("31", "Paiement Auto Airtel / M-Pesa / Orange", "Paiement", "partielle"),
    ("32", "Essai Premium 24h Automatique", "Paiement", "complete"),
    ("33", "Programme Revendeur", "Paiement", "partielle"),
    ("34", "Classement par Quartier / Ville", "Engagement", "a_implanter"),
    ("35", "Alerte Météo Pelouse", "Données", "partielle"),
    ("36", "Mode Duo / Pari à 2", "Engagement", "a_implanter"),
    ("37", "Résumé Vocal / Audio", "Contenu", "a_implanter"),
    ("38", "Historique Face-à-Face Visuel", "Données", "partielle"),
    ("39", "Alerte Underdog", "Paris", "complete"),
    ("40", "Export TikTok / Statut en 1 Clic", "Contenu", "a_implanter"),
    ("41", "Gestion Kelly Automatique", "Gestion du risque", "complete"),
    ("42", "Plan de Mise Fixe / Progressif", "Gestion du risque", "complete"),
    ("43", "Constructeur de Combiné par Risque", "Paris", "complete"),
    ("44", "Double Sûr du Jour", "Paris", "complete"),
    ("45", "Assurance Combiné", "Paris", "a_implanter"),
    ("46", "Cash-Out Partiel Simulé", "Paris", "complete"),
    ("47", "Plan Anti-Perte", "Sécurité", "complete"),
    ("48", "Filtre Réussite par Ligue", "Prédiction", "complete"),
    ("49", "Dashboard ROI Personnel", "Utilisateur", "a_implanter"),
    ("50", "Notifications Heure Kinshasa", "Distribution", "partielle"),
    ("51", "Résumé Vocal IA 30s", "Contenu", "a_implanter"),
    ("52", "Commentaire Live IA", "Live", "a_implanter"),
    ("53", "Débrief Auto Après-Match", "Prédiction", "complete"),
    ("54", "Checklist Avant de Parier", "Sécurité", "complete"),
    ("55", "Base Blessés / Suspendus", "Données", "partielle"),
    ("56", "Compo Prédite vs Officielle", "Données", "partielle"),
    ("57", "Effet Altitude / Voyage", "Données", "partielle"),
    ("58", "Fatigue Calendrier", "Données", "complete"),
    ("59", "Détecteur de Derby / Rivalité", "Données", "complete"),
    ("60", "Indice de Motivation", "Données", "partielle"),
    ("61", "Tactique Entraîneur", "Données", "partielle"),
    ("62", "xG + xA + xPoints", "Prédiction", "partielle"),
    ("63", "Elo Live qui Bouge", "Live", "complete"),
    ("64", "Simulation Monte Carlo 10.000x", "Prédiction", "complete"),
    ("65", "Explication du Prono", "Prédiction", "partielle"),
    ("66", "Backtest de Ta Stratégie", "Prédiction", "complete"),
    ("67", "Paris Virtuels Argent Fictif", "Engagement", "a_implanter"),
    ("68", "Ligue Privée Entre Amis", "Engagement", "a_implanter"),
    ("69", "Bataille IA vs Humains", "Engagement", "partielle"),
    ("70", "Boutique XP", "Engagement", "partielle"),
    ("71", "Bonus Connexion Quotidienne", "Engagement", "complete"),
    ("72", "Roue Quotidienne Gratuite", "Engagement", "complete"),
    ("73", "Classement Parrains", "Affiliation", "complete"),
    ("74", "Lien d'Affiliation Suivi", "Affiliation", "partielle"),
    ("75", "Sync Auto Canal WhatsApp", "Distribution", "a_implanter"),
    ("76", "Post Auto Facebook", "Distribution", "a_implanter"),
    ("77", "Générateur Légende TikTok", "Contenu", "a_implanter"),
    ("78", "Template Story Instagram", "Contenu", "a_implanter"),
    ("79", "Rapport Mensuel PDF", "Utilisateur", "a_implanter"),
    ("80", "Résumé Email Hebdo", "Distribution", "a_implanter"),
    ("81", "Notifications Silencieuses", "Distribution", "partielle"),
    ("82", "Mode Swahili", "Expérience", "a_implanter"),
    ("83", "Commande Vocale", "Expérience", "a_implanter"),
    ("84", "Recherche par Emoji", "Expérience", "a_implanter"),
    ("85", "Alertes Équipe Favorite Ultra-Ciblée", "Distribution", "a_implanter"),
    ("86", "Sync Calendrier Google", "Expérience", "a_implanter"),
    ("87", "Graphique Évolution des Cotes", "Paris", "partielle"),
    ("88", "Mode Nuit / Économie Data", "Expérience", "a_implanter"),
    ("89", "Détecteur de Match Truqué Suspect", "Sécurité", "a_implanter"),
    ("90", "Mode Expert Débloquable", "Abonnement", "a_implanter"),
    ("91", "Dashboard Admin Temps Réel", "Administration", "complete"),
    ("92", "Gestion Utilisateurs par Statut", "Administration", "partielle"),
    ("93", "Recherche Utilisateur", "Administration", "partielle"),
    ("94", "Bannir / Débannir en 1 Clic", "Administration", "complete"),
    ("95", "Offrir Premium Manuellement", "Administration", "complete"),
    ("96", "Prolonger / Raccourcir Abonnement", "Administration", "complete"),
    ("97", "Historique Paiements par Utilisateur", "Paiement", "complete"),
    ("98", "Vérification Paiement Mobile Money Auto", "Paiement", "partielle"),
    ("99", "Générateur de Codes en Masse", "Administration", "complete"),
    ("100", "Codes par Lot / Campagne", "Administration", "partielle"),
    ("101", "Codes Usage Unique / Multi-Usage", "Paiement", "complete"),
    ("102", "Codes avec Date d'Expiration", "Paiement", "partielle"),
    ("103", "Tableau de Bord Revenus", "Administration", "complete"),
    ("104", "Graphique Croissance Abonnés", "Administration", "complete"),
    ("105", "Taux de Conversion Gratuit -> Premium", "Administration", "complete"),
    ("106", "Alerte Churn", "Administration", "complete"),
    ("107", "Offre de Relance Auto", "Distribution", "a_implanter"),
    ("108", "Broadcast Ciblé", "Distribution", "partielle"),
    ("109", "Broadcast Programmé", "Distribution", "partielle"),
    ("110", "Broadcast avec Boutons", "Distribution", "partielle"),
    ("111", "Statistiques de Broadcast", "Distribution", "a_implanter"),
    ("112", "Modération Mots Interdits", "Modération", "complete"),
    ("113", "Anti-Spam Auto", "Modération", "complete"),
    ("114", "Journal d'Activité Admin", "Administration", "complete"),
    ("115", "Rôles Admin", "Administration", "partielle"),
    ("116", "Panneau Pronos Manuel", "Administration", "partielle"),
    ("117", "Validation Pronos Avant Envoi", "Administration", "partielle"),
    ("118", "Corriger un Résultat", "Administration", "partielle"),
    ("119", "Annuler / Reporter un Match", "Administration", "a_implanter"),
    ("120", "Gestion des Ligues Actives", "Administration", "partielle"),
    ("121", "Gestion des Marchés Actifs", "Administration", "partielle"),
    ("122", "Seuils de Confiance Réglables", "Administration", "partielle"),
    ("123", "Mode Maintenance", "Administration", "partielle"),
    ("124", "Message de Bienvenue Personnalisable", "Administration", "partielle"),
    ("125", "FAQ Dynamique Admin", "Administration", "partielle"),
    ("126", "Tickets Support avec Statut", "Support", "partielle"),
    ("127", "Réponses Rapides Admin", "Support", "partielle"),
    ("128", "Export Utilisateurs CSV / Excel", "Administration", "partielle"),
    ("129", "Export Revenus pour Compta", "Administration", "complete"),
    ("130", "Sauvegarde Manuelle en 1 Clic", "Administration", "complete"),
    ("131", "Restauration Backup", "Administration", "partielle"),
    ("132", "Logs d'Erreurs Lisibles", "Administration", "partielle"),
    ("133", "Alerte Admin si API Morte", "Administration", "complete"),
    ("134", "Alerte si Pic d'Erreurs", "Administration", "complete"),
    ("135", "Contrôle Consommation API", "Administration", "complete"),
    ("136", "Gestion des Sources Prioritaires", "Administration", "partielle"),
    ("137", "Planificateur de Tâches", "Administration", "partielle"),
)


def obtenir_catalogue():
    catalogue = {
        feature_id: {
            "nom": nom,
            "groupe": groupe,
            "statut": statut,
        }
        for feature_id, nom, groupe, statut in FEATURES
    }

    try:
        from core.catalog.catalogue_extensions import charger_extensions
        catalogue.update(charger_extensions())
    except Exception:
        pass

    statuts_complets = {
        "138", "139", "149", "150", "163", "164", "165", "168",
        "179", "182", "186", "187", "188", "189", "190", "193",
        "413", "414", "416", "417", "418", "422", "423", "424",
        "432", "433", "434", "435", "436", "437", "438", "439",
        "444", "445", "446", "447", "448", "449", "450", "455",
        "456", "464", "465", "466", "467", "625", "627", "628",
        "631", "632", "633", "634", "635", "637", "638", "639",
        "640", "641", "642", "643", "645", "646", "647", "648", "649",
    }
    for feature_id in statuts_complets:
        if feature_id in catalogue:
            catalogue[feature_id]["statut"] = "complete"
    return catalogue


def obtenir_fonctionnalite(numero):
    feature_id = str(numero)
    catalogue = obtenir_catalogue()
    if feature_id not in catalogue:
        raise KeyError(f"Fonctionnalité inconnue : {feature_id}")
    return catalogue[feature_id]


def lister_par_statut(statut):
    return [
        {"feature_id": feature_id, **item}
        for feature_id, item in obtenir_catalogue().items()
        if item["statut"] == statut
    ]
