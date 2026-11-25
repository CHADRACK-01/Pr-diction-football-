# core/domaine.py
"""
Structures métier typées du bot de pronostics football.

Ces dataclasses servent de contrats d'échange entre les couches :
prédiction, paris, risque, utilisateurs et Telegram. Elles sont immuables
(frozen=True) pour éviter les effets de bord et valident leurs invariants
dans ``__post_init__``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Match:
    """Représente un match de football avec ses données de base."""

    home_team: str
    away_team: str
    competition: str
    date: str  # YYYY-MM-DD
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    cote_home: Optional[float] = None
    cote_draw: Optional[float] = None
    cote_away: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.home_team or not self.away_team:
            raise ValueError("Les noms des équipes ne peuvent pas être vides.")
        if self.cote_home is not None and self.cote_home <= 1.0:
            raise ValueError("La cote domicile doit être > 1.0.")
        if self.cote_draw is not None and self.cote_draw <= 1.0:
            raise ValueError("La cote nul doit être > 1.0.")
        if self.cote_away is not None and self.cote_away <= 1.0:
            raise ValueError("La cote extérieur doit être > 1.0.")


@dataclass(frozen=True)
class Probabilites1N2:
    """Probabilités normalisées pour le marché 1N2 (somme = 1)."""

    p_home: float
    p_draw: float
    p_away: float

    def __post_init__(self) -> None:
        for nom, valeur in (("p_home", self.p_home), ("p_draw", self.p_draw), ("p_away", self.p_away)):
            if not (0.0 <= valeur <= 1.0):
                raise ValueError(f"{nom} doit être compris entre 0 et 1, trouvé {valeur}.")
        total = self.p_home + self.p_draw + self.p_away
        if abs(total - 1.0) > 0.02:
            raise ValueError(f"La somme des probabilités doit être 1.0, trouvé {total:.6f}.")

    @property
    def favori(self) -> str:
        """Retourne 'home', 'draw' ou 'away' selon la probabilité la plus élevée."""
        if self.p_home >= self.p_draw and self.p_home >= self.p_away:
            return "home"
        if self.p_draw >= self.p_away:
            return "draw"
        return "away"

    @property
    def confiance(self) -> float:
        """Probabilité de l'issue la plus probable (niveau de confiance)."""
        return max(self.p_home, self.p_draw, self.p_away)


@dataclass(frozen=True)
class Prediction:
    """Résultat complet d'une prédiction sur un match."""

    match: Match
    probabilites: Probabilites1N2
    score_predit: Optional[str] = None  # ex: "2-1"
    source: str = "modele_ia"  # 'modele_ia', 'poisson', 'manuel'
    date_generation: datetime = field(default_factory=datetime.now)
    valeur_attendue: Optional[float] = None  # EV si cote book connue
    is_value_bet: bool = False
    cote_book: Optional[float] = None

    def est_fiable(self, seuil_confiance: float = 0.60) -> bool:
        """Indique si la prédiction atteint le seuil de confiance."""
        return self.probabilites.confiance >= seuil_confiance


@dataclass(frozen=True)
class ValueBetVerdict:
    """Verdict de value bet pour une issue donnée."""

    label: str
    proba: float
    cote_book: float
    ev: float
    is_value: bool
    seuil_ev: float = 0.05

    def __post_init__(self) -> None:
        if not (0.0 <= self.proba <= 1.0):
            raise ValueError(f"proba doit être dans [0,1], trouvé {self.proba}.")
        if self.cote_book <= 1.0:
            raise ValueError("cote_book doit être > 1.0.")


@dataclass(frozen=True)
class Bankroll:
    """État de la bankroll d'un utilisateur."""

    user_id: int
    montant_total: float
    strategie: str = "kelly_fractionne"
    pourcentage_mise: float = 2.0  # % de la bankroll par pari

    def __post_init__(self) -> None:
        if self.montant_total < 0:
            raise ValueError("montant_total ne peut pas être négatif.")
        if not (0.0 < self.pourcentage_mise <= 10.0):
            raise ValueError("pourcentage_mise doit être dans (0, 10].")

    def plafond_mise(self) -> float:
        """Retourne le montant maximal autorisé pour un pari."""
        return self.montant_total * self.pourcentage_mise / 100.0


@dataclass(frozen=True)
class Utilisateur:
    """Profil utilisateur simplifié."""

    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    statut: str = "free"  # free, premium, expire, bloque, VIP, revendeur
    langue: str = "fr"
    date_expiration: Optional[str] = None
    notifications_actives: bool = True

    @property
    def est_premium(self) -> bool:
        return self.statut == "premium" and self.date_expiration is not None
