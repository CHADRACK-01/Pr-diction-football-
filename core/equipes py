# core/equipes.py
"""
Identification des équipes par une clé canonique.

Deux noms ont la même clé s'ils ne diffèrent que par la casse, les accents,
la ponctuation ou les suffixes de club (FC, CF, AC, SC...).

Règles :
- aucune fusion automatique : on signale les doublons probables, l'admin décide ;
- un nom inconnu reste inconnu (pas de devinette).
"""
import re
import unicodedata
from collections import defaultdict

_SUFFIXES = {"fc", "cf", "ac", "sc", "afc", "cd", "ud", "sv", "fk", "bc", "cfc", "1909", "1846", "1848", "1913"}


def cle_canonique(nom):
    """Clé de comparaison d'un nom d'équipe (sans accents, sans suffixes de club)."""
    if not nom:
        return ""
    s = unicodedata.normalize("NFKD", str(nom))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    mots = [m for m in s.split() if m not in _SUFFIXES]
    return " ".join(mots)


def doublons_probables(noms):
    """Regroupe les noms qui ont la même clé canonique (candidats à fusion, à valider)."""
    groupes = defaultdict(set)
    for n in noms:
        if n:
            groupes[cle_canonique(n)].add(n)
    return {k: sorted(v) for k, v in groupes.items() if len(v) > 1 and k}


def rapport_doublons(noms):
    """Texte lisible pour l'admin."""
    dup = doublons_probables(noms)
    if not dup:
        return "Aucun doublon probable détecté."
    lignes = [f"{len(dup)} doublon(s) probable(s) à valider :"]
    for cle, variantes in sorted(dup.items()):
        lignes.append(f"- {' | '.join(variantes)}")
    return "\n".join(lignes)
