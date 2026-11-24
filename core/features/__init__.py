# core/features/__init__.py
"""
Package des fonctionnalités "décor" (stubs) du bot Prédiction Football.

Chaque module de ce package contient des implémentations squelettes
(stubs) pour les fonctionnalités listées dans le README et le catalogue
core/catalog/catalogue_fonctionnalites.py.

Tous les stubs suivent le même contrat :
    - Accepte *args, **kwargs (flexible pour tout type d'appel)
    - Retourne un dict avec au minimum la clé "status"
    - Logge l'appel via core.utils.logs
    - Contient un commentaire # TODO indiquant ce qu'il faut implémenter

Statuts de retour possibles :
    - "a_implanter" : fonctionnalité non encore implémentée
    - "partielle"   : squelette présent, logique à compléter
    - "complete"    : fonctionnalité opérationnelle (rare dans ce package)

Exemple :
    >>> from core.features.alertes import detecteur_value_bet
    >>> detecteur_value_bet(match_id=42, cote=2.10)
    {"status": "a_implanter", "feature_id": 2, "message": "..."}
"""

from core.utils.logs import log_info

log_info("Package core.features initialisé (stubs/décors)", "FEATURES")

__all__ = [
    "alertes",
    "cotes",
    "matchs",
    "cashout",
    "langue",
    "historique",
    "filtres",
    "marches",
    "calendrier",
    "ticket",
    "engagement",
    "hors_ligne",
    "comparateurs",
    "reseaux_sociaux",
    "jeu_responsable",
    "vip",
    "competitions",
    "stats",
    "coach",
    "xg",
    "equipes",
    "interface",
    "paiements",
    "premium",
    "revendeur",
    "classements",
    "conditions",
    "audio",
    "bankroll",
    "combines",
    "dashboard",
    "notifications",
    "debrief",
    "elo",
    "simulation",
    "explication",
    "backtest",
    "virtuel",
    "bataille",
    "boutique",
    "parrainage",
    "affiliation",
    "rapports",
    "admin",
    "codes",
    "revenus",
    "broadcast",
    "moderation",
    "support",
    "export",
    "sauvegarde",
    "logs",
    "scheduler",
    "commandes_locales",
]
