# core/features.py
"""
Calcul des features, utilisé à l'entraînement ET en production.

Règle centrale : pour un match à la date D, les features n'utilisent que
les matchs de date STRICTEMENT antérieure à D. C'est ce qui empêche la fuite
de données (les statistiques du match lui-même ne sont jamais utilisées).

Usage :
    etat = EtatEquipes()
    for match in historique_trié_par_date:
        features = etat.predire(match["home"], match["away"], match["date"])  # AVANT
        etat.mettre_a_jour(match)                                              # APRÈS
"""
import datetime as _dt

from core.contrat_modele import (
    ELO_AVANTAGE_DOMICILE,
    ELO_INITIAL,
    ELO_K,
    FENETRE_FORME,
    FEATURE_NAMES,
    MIN_MATCHS_HISTORIQUE,
    REPOS_MAX_JOURS,
)


def _jour(date):
    """Normalise une date en objet date. Accepte 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'."""
    if isinstance(date, _dt.date):
        return date if not isinstance(date, _dt.datetime) else date.date()
    return _dt.date.fromisoformat(str(date)[:10])


def _points(resultat):
    return {"H": 1.0, "D": 0.5, "A": 0.0}[resultat]


class EtatEquipes:
    def __init__(self):
        self.elo = {}        # équipe -> rating
        self.nb = {}         # équipe -> nombre de matchs vus
        self.recents = {}    # équipe -> liste des derniers (points, marques, encaisses)
        self.dernier_jour = {}  # équipe -> date du dernier match (ISO)
        self.date_max = None    # dernière date vue (ISO)

    # ---------- mise à jour (après le match) ----------
    def mettre_a_jour(self, match):
        dom, ext = match["home"], match["away"]
        fthg, ftag, ftr = int(match["fthg"]), int(match["ftag"]), match["ftr"]
        jour = _jour(match["date"]).isoformat()

        r_dom = self.elo.get(dom, ELO_INITIAL)
        r_ext = self.elo.get(ext, ELO_INITIAL)
        attendu_dom = 1.0 / (1.0 + 10 ** ((r_ext - (r_dom + ELO_AVANTAGE_DOMICILE)) / 400.0))
        score_dom = {"H": 1.0, "D": 0.5, "A": 0.0}[ftr]
        self.elo[dom] = r_dom + ELO_K * (score_dom - attendu_dom)
        self.elo[ext] = r_ext + ELO_K * ((1.0 - score_dom) - (1.0 - attendu_dom))

        self._ajouter(dom, _points(ftr), fthg, ftag, jour)
        self._ajouter(ext, _points({"H": "A", "D": "D", "A": "H"}[ftr]), ftag, fthg, jour)

        if self.date_max is None or jour > self.date_max:
            self.date_max = jour

    def _ajouter(self, equipe, points, marques, encaisses, jour):
        self.nb[equipe] = self.nb.get(equipe, 0) + 1
        liste = self.recents.setdefault(equipe, [])
        liste.append([points, marques, encaisses])
        del liste[:-FENETRE_FORME]
        self.dernier_jour[equipe] = jour

    # ---------- prédiction (avant le match) ----------
    def predire(self, dom, ext, date):
        """Renvoie le dict de features pour dom-ext à la date donnée, ou None si
        l'historique est insuffisant. N'modifie pas l'état."""
        for equipe in (dom, ext):
            if self.nb.get(equipe, 0) < MIN_MATCHS_HISTORIQUE:
                return None

        jour = _jour(date)
        f = {}
        elo_dom = self.elo.get(dom, ELO_INITIAL)
        elo_ext = self.elo.get(ext, ELO_INITIAL)
        f["elo_home"] = elo_dom
        f["elo_away"] = elo_ext
        f["elo_diff"] = elo_dom - elo_ext

        forme_dom, marques_dom, encaisses_dom = self._moyennes(dom)
        forme_ext, marques_ext, encaisses_ext = self._moyennes(ext)
        f["forme_h"] = forme_dom
        f["forme_a"] = forme_ext
        f["forme_diff"] = forme_dom - forme_ext
        f["marques_h"] = marques_dom
        f["encaisses_h"] = encaisses_dom
        f["marques_a"] = marques_ext
        f["encaisses_a"] = encaisses_ext

        repos_dom = self._repos(dom, jour)
        repos_ext = self._repos(ext, jour)
        f["repos_h"] = repos_dom
        f["repos_a"] = repos_ext
        f["repos_diff"] = repos_dom - repos_ext

        return {nom: float(f[nom]) for nom in FEATURE_NAMES}

    def _moyennes(self, equipe):
        liste = self.recents.get(equipe, [])
        n = len(liste)
        return (
            sum(p for p, _, _ in liste) / n,
            sum(m for _, m, _ in liste) / n,
            sum(e for _, _, e in liste) / n,
        )

    def _repos(self, equipe, jour):
        dernier = self.dernier_jour.get(equipe)
        if dernier is None:
            return float(REPOS_MAX_JOURS)
        ecart = (jour - _dt.date.fromisoformat(dernier)).days
        return float(min(max(ecart, 0), REPOS_MAX_JOURS))

    # ---------- sérialisation (pour models_cache) ----------
    def vers_dict(self):
        return {
            "elo": dict(self.elo),
            "nb": dict(self.nb),
            "recents": {k: [list(x) for x in v] for k, v in self.recents.items()},
            "dernier_jour": dict(self.dernier_jour),
            "date_max": self.date_max,
        }

    @classmethod
    def depuis_dict(cls, d):
        e = cls()
        e.elo = {k: float(v) for k, v in d.get("elo", {}).items()}
        e.nb = {k: int(v) for k, v in d.get("nb", {}).items()}
        e.recents = {k: [list(x) for x in v] for k, v in d.get("recents", {}).items()}
        e.dernier_jour = dict(d.get("dernier_jour", {}))
        e.date_max = d.get("date_max")
        return e
