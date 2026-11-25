# core/features/__init__.py
"""
Package des fonctionnalités (stubs de compatibilité).

Ce package ne contient plus d'implémentations directes. Toutes les
fonctionnalités ont été déplacées vers leurs packages canoniques :

- core.betting.*     : paris, cashout, bankroll, gestion_risques, value_bet
- core.predictions.* : poisson, nouveau_prediction, ml_model, backtest
- core.administration.* : alertes_live, pic_erreurs, controle_quota, dashboard
- core.services.*    : prediction, paris, risque, engagement, paiement
- core.adaptateurs.* : api_football, paiements, reseaux_sociaux, audio, meteo

Ce module est conservé pour la rétrocompatibilité des imports.
"""

from __future__ import annotations

__all__ = []
