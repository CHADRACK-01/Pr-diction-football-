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
    # ===== Paris & Value Bet =====
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
        "note": "Gestion Kelly automatique, calcul de mise selon bankroll.",
    },
    "42": {
        "impl_module": "core.betting.bankroll",
        "impl_function": "plan_mise_progresif",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Plan de mise fixe, Martingale douce, Fibonacci.",
    },
    "43": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "generer_combine_par_risque",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Constructeur de combiné par risque, nécessite cotes bookmaker.",
    },
    "44": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "double_sur_du_jour",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Double sûr du jour (2 matchs forte confiance).",
    },
    "45": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "assurance_combine",
        "dependances_externes": [],
        "statut_impl": "a_implanter",
        "note": "Assurance combiné : calcul des gains si quelques sélections échouent.",
    },
    "46": {
        "impl_module": "core.betting.cashout",
        "impl_function": "cashout_partiel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Cash-out partiel simulé.",
    },
    "47": {
        "impl_module": "core.betting.gestion_risques",
        "impl_function": "plan_anti_perte",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Plan anti-perte : bloque les gros combinés après série de pertes.",
    },
    "48": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "filtre_reussite_par_ligue",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Filtre de réussite par ligue, performances historiques.",
    },
    "89": {
        "impl_module": "core.betting.paris_builder",
        "impl_function": "detecter_match_suspect",
        "dependances_externes": ["api_football"],
        "statut_impl": "a_implanter",
        "note": "Détecteur de match truqué suspect (cotes étranges).",
    },

    # ===== Prédiction & Modèle ML =====
    "1": {
        "impl_module": "core.administration.alertes_live",
        "impl_function": "verifier_buts_live",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Alertes live buts, nécessite API-Football pour les scores en direct.",
    },
    "26": {
        "impl_module": "core.predictions.ml_model",
        "impl_function": "charger_et_entrainer",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Modèle xG / IA, chargement du bundle depuis models_cache (Turso).",
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
    "90": {
        "impl_module": "core.features.expert",
        "impl_function": "activer_mode_expert",
        "dependances_externes": [],
        "statut_impl": "a_implanter",
        "note": "Mode expert débloquable (xG, Elo, Monte Carlo après 30 jours).",
    },

    # ===== Paiements & Abonnements =====
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

    # ===== Données Sportives (API) =====
    "4": {
        "impl_module": "core.services.compo",
        "impl_function": "verifier_compo_officielle",
        "dependances_externes": ["api_football"],
        "statut_impl": "a_implanter",
        "note": "Alerte compo officielle / absents, nécessite API-Football.",
    },
    "18": {
        "impl_module": "core.services.championnats",
        "impl_function": "liste_championnats_africains",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Pronostics championnats africains (Linafoot, CAN, CAF, Afrique du Sud).",
    },
    "25": {
        "impl_module": "core.services.arbitre",
        "impl_function": "stats_arbitre",
        "dependances_externes": ["api_football"],
        "statut_impl": "a_implanter",
        "note": "Stats arbitres, cartons moyens, données pour marchés cartons.",
    },
    "27": {
        "impl_module": "core.services.transferts",
        "impl_function": "impact_transferts_entraineurs",
        "dependances_externes": ["api_football"],
        "statut_impl": "a_implanter",
        "note": "Impact des transferts et changements d'entraîneur.",
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
    "87": {
        "impl_module": "core.services.cotes",
        "impl_function": "graphique_evolution_cotes",
        "dependances_externes": ["api_football"],
        "statut_impl": "partielle",
        "note": "Graphique d'évolution des cotes sur 24h+.",
    },

    # ===== Expérience Utilisateur (Langue, Audio, Réseaux) =====
    "6": {
        "impl_module": "core.features.langue",
        "impl_function": "mode_lingala_francais",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Mode Lingala + Français (et Swahili), changement de langue.",
    },
    "37": {
        "impl_module": "core.adaptateurs.audio",
        "impl_function": "AdaptateurAudio.generer_audio",
        "dependances_externes": ["tts"],
        "statut_impl": "a_implanter",
        "note": "Résumé vocal / audio, nécessite clé TTS.",
    },
    "82": {
        "impl_module": "core.features.langue",
        "impl_function": "mode_swahili",
        "dependances_externes": [],
        "statut_impl": "a_implanter",
        "note": "Mode Swahili (Est de la RDC).",
    },
    "86": {
        "impl_module": "core.adaptateurs.calendrier",
        "impl_function": "AdaptateurCalendrier.creer_evenement",
        "dependances_externes": ["google_calendar"],
        "statut_impl": "a_implanter",
        "note": "Synchronisation Google Calendar, nécessite credentials Google.",
    },
    "91": {
        "impl_module": "core.administration.dashboard_admin",
        "impl_function": "dashboard_admin_temps_reel",
        "dependances_externes": [],
        "statut_impl": "complete",
        "note": "Dashboard administrateur temps réel (utilisateurs, pronos, paiements).",
    },

    # ===== Distribution & Réseaux Sociaux =====
    "75": {
        "impl_module": "core.adaptateurs.reseaux_sociaux",
        "impl_function": "AdaptateurReseauxSociaux.publier_texte",
        "dependances_externes": ["telegram", "whatsapp"],
        "statut_impl": "a_implanter",
        "note": "Sync auto canal WhatsApp, nécessite configuration WhatsApp Business.",
    },
    "76": {
        "impl_module": "core.adaptateurs.reseaux_sociaux",
        "impl_function": "AdaptateurReseauxSociaux.publier_texte",
        "dependances_externes": ["facebook"],
        "statut_impl": "a_implanter",
        "note": "Publication auto Facebook, nécessite page Facebook + token.",
    },
    "77": {
        "impl_module": "core.features.reseaux_sociaux",
        "impl_function": "generer_legende_tiktok",
        "dependances_externes": [],
        "statut_impl": "a_implanter",
        "note": "Générateur de légendes TikTok avec hashtags locaux.",
    },
    "78": {
        "impl_module": "core.features.reseaux_sociaux",
        "impl_function": "template_story_instagram",
        "dependances_externes": [],
        "statut_impl": "a_implanter",
        "note": "Template story Instagram 9:16 avec logo et ticket.",
    },
    "95": {
        "impl_module": "core.adaptateurs.reseaux_sociaux",
        "impl_function": "AdaptateurReseauxSociaux.publier_texte",
        "dependances_externes": ["telegram"],
        "statut_impl": "complete",
        "note": "Diffusion des pronostics sur le canal Telegram.",
    },

    # ===== Administration =====
    "92": {
        "impl_module": "core.administration.utilisateurs",
        "impl_function": "gestion_utilisateurs_statut",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Gestion utilisateurs par statut (gratuit, Premium, expiré, bloqué, VIP, revendeur).",
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
    "137": {
        "impl_module": "core.administration.planificateur",
        "impl_function": "planificateur_taches",
        "dependances_externes": [],
        "statut_impl": "partielle",
        "note": "Planificateur de tâches (entraînement modèle, tâches récurrentes).",
    },
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
