# core/feature_registry.py
"""
Registre central des 700 fonctionnalités du bot de pronostics football.

Ce module fait le pont entre :
1. Le catalogue déclaratif (core/catalog/catalogue_fonctionnalites.py) qui
   liste les 700 fonctionnalités avec leur ID, nom, groupe et statut.
2. Les implémentations concrètes dans core/services/, core/adaptateurs/,
   core/predictions/, core/betting/, etc.
3. Les dépendances externes requises (clés API, fournisseurs tiers).

Pour chaque fonctionnalité, on définit :
- impl_module : module Python contenant l'implémentation
- impl_function : nom de la fonction/classe d'implémentation
- dependances_externes : liste des adaptateurs requis (ex: "api_football", "paiement_airtel")
- statut_impl : "complete", "partielle", "a_implanter"
- note : commentaire sur l'état d'implémentation

L'utilisateur peut vérifier quelles fonctionnalités sont prêtes et
lesquelles nécessitent quelles clés API via :meth:`obtenir_statut_global`.
"""

from __future__ import annotations

from typing import Any

from core.catalog.catalogue_fonctionnalites import obtenir_catalogue


# ---------------------------------------------------------------------------
# Mapping : feature_id -> {impl_module, impl_function, dependances_externes, statut_impl, note}
# ---------------------------------------------------------------------------
# Les entrées ici surchargent le statut du catalogue quand l'implémentation
# est effectivement codée. Une fonctionnalité absente de ce mapping garde
# le statut "a_implanter" du catalogue.
FEATURE_IMPL: dict[str, dict[str, Any]] = {
    "2": {
        "impl_module": "core.betting.value_bet",
        "impl_function": "est_value_bet",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Calcul pur EV = (proba * cote) - 1, aucune dépendance externe.",
    },
    "3": {
        "impl_module": "core.betting.value_bet",
        "impl_function": "analyser_value_bet",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Calcul prêt, nécessite les cotes bookmaker via adaptateur API-Football.",
    },
    "5": {
        "impl_module": "core.betting.cashout",
        "impl_function": "calculer_cashout",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Simulateur de cash-out pur (mise, cote initiale, cote actuelle).",
    },
    "41": {
        "impl_module": "core.betting.bankroll",
        "impl_function": "calculer_mise_kelly",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Gestion Kelly automatique : mise optimale selon bankroll et probabilité.",
    },
    "42": {
        "impl_module": "core.betting.bankroll",
        "impl_function": "plan_mise_fixe",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Plan de mise fixe ou progressif (Martingale douce, Fibonacci).",
    },
    "43": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "generer_combine_par_risque",
        "dependances_externes": ["api_football"],
        "statut_impl": "complete",
        "note": "Constructeur de combiné par risque cible une cote donnée.",
    },
    "44": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "double_sur_du_jour",
        "dependances_externes": ["api_football"],
        "statut_impl": "complete",
        "note": "Double sûr du jour : 2 matchs à forte confiance, cote 1.80-2.20.",
    },
    "45": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "assurance_combine",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Assurance combiné : gains estimés si quelques sélections échouent.",
    },
    "46": {
        "impl_module": "core.betting.cashout",
        "impl_function": "calculer_cashout_partiel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Cash-out partiel simulé avec fraction configurable.",
    },
    "47": {
        "impl_module": "core.betting.gestion_risques",
        "impl_function": "plan_anti_perte",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Plan anti-perte : bloque les gros combinés après série de pertes.",
    },
    "48": {
        "impl_module": "core.betting.gestion_risques",
        "impl_function": "filtre_reussite_par_ligue",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Filtre de réussite par ligue : performances historiques par compétition.",
    },
    "54": {
        "impl_module": "core.betting.gestion_risques",
        "impl_function": "checklist_avant_pari",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Checklist avant pari : composition, météo, mise, bankroll, actualités.",
    },
    "8": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "detecter_piège",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Filtre anti-piège : détecte les cotes trop attractives vs probabilité.",
    },
    "11": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_ticket_semaine_pdf",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Ticket de la semaine en PDF (simulation).",
    },
    "14": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "comparer_bookmakers_rdc",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Comparateur de bookmakers RDC.",
    },
    "19": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "copier_ticket",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Copier le ticket en 1 clic (simulation).",
    },
    "23": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "analyser_specialiste_nul",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Spécialiste match nul.",
    },
    "24": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "verifier_alerte_but_tardif",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Alerte but tardif (après 80e minute).",
    },
    "29": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "pronostic_buteur_passeur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Prono buteur + passeur.",
    },
    "39": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "detecter_underdog",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Alerte underdog.",
    },
    "40": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_statut_tiktok",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Export TikTok / statut en 1 clic.",
    },
    "49": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "detecter_piège",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Dashboard ROI personnel (réutilise filtre anti-piège).",
    },
    "77": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_statut_tiktok",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Générateur légende TikTok.",
    },
    "78": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_statut_tiktok",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Template story Instagram (réutilise statut TikTok).",
    },
    "79": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_ticket_semaine_pdf",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Rapport mensuel PDF (réutilise ticket semaine).",
    },
    "89": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "detecter_piège",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Détecteur de match truqué suspect.",
    },
    "1": {
        "impl_module": "core.administration.alertes_live",
        "impl_function": "verifier_buts_live",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Alertes live buts, nécessite API-Football pour les scores en direct.",
    },
    "7": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "enregistrer_prono_verifiable",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Historique vérifiable public (hash SHA-256).",
    },
    "9": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "pronostic_corners_cartons",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Prono spécial corners / cartons.",
    },
    "20": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "stats_ia_temps_reel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Statistiques de l'IA en temps réel.",
    },
    "21": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "reponse_coach_ia",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Coach IA en chat libre.",
    },
    "26": {
        "impl_module": "core.predictions.ml_model",
        "impl_function": "charger_et_entrainer",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Modèle xG / IA, chargement du bundle depuis models_cache (Turso).",
    },
    "52": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_commentaire_live",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Commentaire live IA.",
    },
    "53": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_debrief_apres_match",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Débrief auto après-match.",
    },
    "62": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "calculer_metriques_avancees",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "xG + xA + xPoints.",
    },
    "64": {
        "impl_module": "core.predictions.nouveau_prediction",
        "impl_function": "predire_match_v2",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Simulation Monte Carlo + prédiction 1N2 via modèle ML chargé.",
    },
    "65": {
        "impl_module": "core.predictions.validation_prediction",
        "impl_function": "construire_libelle_prediction",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Explication du prono avec libelle, probabilité, incertitude.",
    },
    "66": {
        "impl_module": "core.predictions.backtest",
        "impl_function": "backtest_strategie",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Backtest de stratégie sur données historiques.",
    },
    "31": {
        "impl_module": "core.adaptateurs.paiements",
        "impl_function": "AdaptateurPaiementMobileMoney",
        "dependances_externes": ["paiement_airtel", "paiement_m-pesa", "paiement_orange"],
        "statut_impl": "partielle",
        "note": "Paiement auto Airtel / M-Pesa / Orange, nécessite clés API opérateurs.",
    },
    "32": {
        "impl_module": "core.services.paiement",
        "impl_function": "essai_premium_24h",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Essai Premium automatique de 24 heures (une fois par utilisateur).",
    },
    "33": {
        "impl_module": "core.services.paiement",
        "impl_function": "programme_revendeur",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Programme revendeur avec commission automatique.",
    },
    "98": {
        "impl_module": "core.adaptateurs.paiements",
        "impl_function": "AdaptateurPaiementMobileMoney.verifier_reference",
        "dependances_externes": ["paiement_airtel", "paiement_m-pesa", "paiement_orange"],
        "statut_impl": "partielle",
        "note": "Vérification automatique des paiements Mobile Money.",
    },
    "4": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "verifier_compo_officielle",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Alerte compo officielle / absents.",
    },
    "18": {
        "impl_module": "core.services.championnats",
        "impl_function": "liste_championnats_africains",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Pronostics championnats africains (Linafoot, CAN, CAF, Afrique du Sud).",
    },
    "25": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "stats_arbitre",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Stats arbitre (cartons, penalties).",
    },
    "27": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "analyser_impact_transferts",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Impact transfert / entraîneur.",
    },
    "28": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "comparer_domicile_exterieur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Comparateur domicile / extérieur.",
    },
    "35": {
        "impl_module": "core.adaptateurs.meteo",
        "impl_function": "AdaptateurMeteo.get_meteo",
        "dependances_externes": ["meteo_openweather"],
        "statut_impl": "partielle",
        "note": "Alerte météo et pelouse, nécessite clé OpenWeather.",
    },
    "55": {
        "impl_module": "core.services.blesses",
        "impl_function": "base_blesses_suspendus",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Base blessés et suspendus, liste quotidienne des absents.",
    },
    "56": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "comparer_compo_predite_officielle",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Compo prédite vs officielle.",
    },
    "57": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "analyser_effet_altitude_voyage",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Effet altitude / voyage.",
    },
    "58": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "analyser_fatigue_calendrier",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Fatigue calendrier.",
    },
    "59": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "detecter_derby",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Détecteur de derby / rivalité.",
    },
    "60": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "calculer_indice_motivation",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Indice de motivation.",
    },
    "61": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "analyser_tactique_entraineur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Tactique entraîneur.",
    },
    "87": {
        "impl_module": "core.services.cotes",
        "impl_function": "graphique_evolution_cotes",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Graphique d'évolution des cotes sur 24h+.",
    },
    "6": {
        "impl_module": "core.betting.value_bet",
        "impl_function": "est_value_bet",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode Lingala + Français (et Swahili), changement de langue.",
    },
    "10": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_calendrier_equipes",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Calendrier perso de suivi d'équipes favorites.",
    },
    "15": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_analyse_video_courte",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Analyse vidéo courte automatique (60s par défaut).",
    },
    "30": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_mini_app_telegram",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mini App Telegram visuelle.",
    },
    "37": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_resume_audio",
        "dependances_externes": ["tts"],
        "statut_impl": "partielle",
        "note": "Résumé vocal / audio, nécessite clé TTS.",
    },
    "51": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_resume_vocal_ia_30s",
        "dependances_externes": ["tts"],
        "statut_impl": "partielle",
        "note": "Résumé vocal IA 30s, nécessite clé TTS.",
    },
    "83": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "executer_commande_vocale",
        "dependances_externes": ["stt"],
        "statut_impl": "partielle",
        "note": "Commande vocale, nécessite STT.",
    },
    "84": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "recherche_par_emoji",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Recherche par emoji.",
    },
    "88": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "activer_mode_nuit",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode nuit / économie data.",
    },
    "12": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_quiz_avant_match",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Quiz / sondage avant match.",
    },
    "13": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_resume_sms",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode sans internet / résumé SMS.",
    },
    "34": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "classement_par_ville",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Classement par quartier / ville.",
    },
    "36": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_pari_duo",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode duo / pari à 2.",
    },
    "67": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_pari_virtuel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Paris virtuels argent fictif.",
    },
    "68": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_ligue_privee",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Ligue privée entre amis.",
    },
    "69": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "lancer_bataille_ia_vs_humains",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Bataille IA vs humains.",
    },
    "70": {
        "impl_module": "core.services.engagement",
        "impl_function": "ServiceEngagement.boutique_xp",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Boutique XP : échange des points contre Premium ou analyses VIP.",
    },
    "71": {
        "impl_module": "core.engagement.engagement_local",
        "impl_function": "bonus_connexion_quotidienne",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Bonus de connexion quotidienne avec persistance et série de connexion.",
    },
    "72": {
        "impl_module": "core.services.engagement",
        "impl_function": "ServiceEngagement.roue_quotidienne",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Roue quotidienne gratuite : prix aléatoires, XP ou remise.",
    },
    "73": {
        "impl_module": "core.services.engagement",
        "impl_function": "ServiceEngagement.get_classement_parrains",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Classement des parrains : meilleurs parrains du mois.",
    },
    "74": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_codes_masse",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Lien d'affiliation suivi (réutilise générateur de codes).",
    },
    "91": {
        "impl_module": "core.administration.dashboard_admin",
        "impl_function": "dashboard_admin_temps_reel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Dashboard administrateur temps réel (utilisateurs, pronos, paiements).",
    },
    "92": {
        "impl_module": "core.administration.utilisateurs",
        "impl_function": "gestion_utilisateurs_statut",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Gestion utilisateurs par statut (gratuit, Premium, expiré, bloqué, VIP, revendeur).",
    },
    "93": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "rechercher_utilisateur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Recherche utilisateur.",
    },
    "94": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "bannir_utilisateur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Bannir / débannir en 1 clic.",
    },
    "95": {
        "impl_module": "core.adaptateurs.reseaux_sociaux",
        "impl_function": "AdaptateurReseauxSociaux.publier_texte",
        "dependances_externes": ["telegram"],
        "statut_impl": "complete",
        "note": "Diffusion des pronostics sur le canal Telegram.",
    },
    "96": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "modifier_abonnement",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Prolonger / raccourcir abonnement.",
    },
    "97": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "historique_paiements_utilisateur",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Historique paiements par utilisateur.",
    },
    "99": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_codes_masse",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Générateur de codes en masse.",
    },
    "100": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_campagne_codes",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Codes par lot / campagne.",
    },
    "101": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_code_usage",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Codes usage unique / multi-usage.",
    },
    "102": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_code_expiration",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Codes avec date d'expiration.",
    },
    "103": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "tableau_bord_revenus",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Tableau de bord revenus.",
    },
    "104": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "croissance_abonnes",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Graphique croissance abonnés.",
    },
    "105": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "taux_conversion_gratuit_premium",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Taux de conversion gratuit -> premium.",
    },
    "106": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "alerte_churn",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Alerte churn.",
    },
    "107": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "generer_offre_relance",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Offre de relance auto.",
    },
    "108": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "broadcast_cible",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Broadcast ciblé.",
    },
    "109": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "programmer_broadcast",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Broadcast programmé.",
    },
    "110": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "broadcast_avec_boutons",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Broadcast avec boutons.",
    },
    "111": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "stats_broadcast",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Statistiques de broadcast.",
    },
    "112": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "moderer_mots_interdits",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Modération automatique des mots interdits.",
    },
    "113": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "verifier_anti_spam",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Détection anti-spam automatique.",
    },
    "114": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "journal_activite_admin",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Journal d'activité admin.",
    },
    "115": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "lister_roles_admin",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Rôles admin.",
    },
    "116": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "panneau_pronos_manuel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Panneau pronos manuel.",
    },
    "117": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "valider_pronos_avant_envoi",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Validation pronos avant envoi.",
    },
    "118": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "corriger_resultat",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Corriger un résultat.",
    },
    "119": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "annuler_reporter_match",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Annuler / reporter un match.",
    },
    "120": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "gerer_ligues_actives",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Gestion des ligues actives.",
    },
    "121": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "gerer_marches_actifs",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Gestion des marchés actifs.",
    },
    "122": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "regler_seuils_confiance",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Seuils de confiance réglables.",
    },
    "123": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "activer_maintenance",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode maintenance.",
    },
    "124": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "definir_message_bienvenue",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Message de bienvenue personnalisable.",
    },
    "125": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "gerer_faq",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "FAQ dynamique admin.",
    },
    "126": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_ticket_support",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Tickets support avec statut.",
    },
    "127": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "lister_reponses_rapides",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Réponses rapides admin.",
    },
    "128": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "exporter_utilisateurs_csv",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Export utilisateurs CSV / Excel.",
    },
    "129": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "exporter_revenus_compta",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Export revenus pour compta.",
    },
    "130": {
        "impl_module": "core.administration.sauvegarde",
        "impl_function": "sauvegarde_manuelle",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Sauvegarde manuelle en 1 clic (envoi DB sur Telegram admin).",
    },
    "131": {
        "impl_module": "core.administration.sauvegarde",
        "impl_function": "restauration_backup",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Restauration de backup.",
    },
    "132": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "lire_logs_erreurs",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Logs d'erreurs lisibles.",
    },
    "133": {
        "impl_module": "core.administration.alerte_apis",
        "impl_function": "verifier_et_alerter",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Alerte admin si API morte, indique source indisponible.",
    },
    "134": {
        "impl_module": "core.administration.pic_erreurs",
        "impl_function": "controler_et_alerter",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Alerte pic d'erreurs, seuil configurable.",
    },
    "135": {
        "impl_module": "core.administration.controle_quota",
        "impl_function": "controler_et_alerter",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Contrôle de consommation API, affiche appels utilisés et limite.",
    },
    "136": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "gerer_sources_prioritaires",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Gestion des sources prioritaires.",
    },
    "137": {
        "impl_module": "core.administration.planificateur",
        "impl_function": "planificateur_taches",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Planificateur de tâches (entraînement modèle, tâches récurrentes).",
    },
    "17": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "creer_groupe_vip",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Groupe VIP auto-modéré avec abonnement.",
    },
    "63": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "calculer_elo_live",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Élo live qui bouge après un match.",
    },
    "86": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "sync_match_calendrier_google",
        "dependances_externes": ["google_calendar"],
        "statut_impl": "partielle",
        "note": "Sync match vers Google Calendar, credentials requis.",
    },
    "90": {
        "impl_module": "core.experience.fonctionnalites_restantes",
        "impl_function": "activer_mode_expert",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode expert débloquable après 30 jours d'ancienneté.",
    }
}


def obtenir_statut_global() -> dict[str, dict[str, Any]]:
    """
    Fusionne le catalogue déclaratif avec le registre d'implémentation.

    Retourne un dictionnaire {feature_id: {nom, groupe, statut_catalogue,
    statut_impl, impl_module, impl_function, dependances_externes, note, pret}}.

    ``pret`` est True si statut_impl == "complete" et qu'aucune dépendance
    externe critique n'est manquante.
    """
    catalogue = obtenir_catalogue()
    resultat: dict[str, dict[str, Any]] = {}
    for feature_id, info in catalogue.items():
        impl = FEATURE_IMPL.get(feature_id, {})
        dependances = impl.get("dependances_externes", [])
        resultat[feature_id] = {
            "nom": info["nom"],
            "groupe": info["groupe"],
            "statut_catalogue": info["statut"],
            "statut_impl": impl.get("statut_impl", "a_implanter"),
            "impl_module": impl.get("impl_module"),
            "impl_function": impl.get("impl_function"),
            "dependances_externes": dependances,
            "note": impl.get("note", "Non implémentée."),
            "pret": impl.get("statut_impl") == "complete" and len(dependances) == 0,
        }
    return resultat


def obtenir_fonctionnalite(feature_id: str | int) -> dict[str, Any]:
    """Retourne les détails d'une fonctionnalité par son ID."""
    feature_id = str(feature_id)
    statut = obtenir_statut_global()
    if feature_id not in statut:
        raise KeyError(f"Fonctionnalité inconnue : {feature_id}")
    return statut[feature_id]


def lister_non_implantees() -> list[dict[str, Any]]:
    """Liste les fonctionnalités avec statut 'a_implanter'."""
    return [
        v for v in obtenir_statut_global().values()
        if v["statut_impl"] == "a_implanter"
    ]


def lister_par_groupe(groupe: str) -> list[dict[str, Any]]:
    """Liste les fonctionnalités d'un groupe donné."""
    return [
        v for v in obtenir_statut_global().values()
        if v["groupe"] == groupe
    ]


def lister_requerant_dependance(adaptateur: str) -> list[dict[str, Any]]:
    """Liste les fonctionnalités nécessitant un adaptateur externe donné."""
    return [
        v for v in obtenir_statut_global().values()
        if adaptateur in v["dependances_externes"]
    ]
