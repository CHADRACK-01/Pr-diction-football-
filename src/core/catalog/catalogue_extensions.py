"""Extrait les fonctionnalités supplémentaires 138 à 700 des fichiers docs.

Ce module conserve les descriptions du catalogue comme données documentaires.
Il ne prétend pas les rendre opérationnelles : les statuts restent vérifiables
et explicites dans le catalogue central.
"""

import re
from pathlib import Path


_DOCS = (
    (138, 274, "03_Fonctionnalites_138_a_274.txt", "Extension 138-274"),
    (275, 411, "04_Fonctionnalites_275_a_411.txt", "Extension 275-411"),
    (412, 547, "05_Fonctionnalites_412_a_547.txt", "Extension 412-547"),
    (548, 624, "06_Fonctionnalites_548_a_624.txt", "Extension 548-624"),
    (625, 700, "07_Fonctionnalites_625_a_700.txt", "Extension 625-700"),
)


def _nom_avant_separateur(ligne):
    ligne = ligne.strip()
    ligne = re.sub(r"^\d{3}\s*(?:[.]|—|-)\s*", "", ligne)
    nom = ligne.split("\n", 1)[0].strip()
    if ":" in nom:
        nom = nom.split(":", 1)[0].strip()
    return nom[:180].strip()


def charger_extensions(racine=None):
    racine = Path(racine) if racine else Path(__file__).resolve().parent.parent
    dossier_docs = racine / "docs"
    extensions = {}

    for debut, fin, fichier, groupe in _DOCS:
        chemin = dossier_docs / fichier
        if not chemin.exists():
            continue
        texte = chemin.read_text(encoding="utf-8")

        motifs = (
            re.compile(r"(?m)^\s*(\d{3})\.\s*(.+)$"),
            re.compile(r"(?m)^\s*(\d{3})\s*[—-]\s*(.+)$"),
        )
        trouvees = {}
        for motif in motifs:
            for numero, suite in motif.findall(texte):
                identifiant = int(numero)
                if debut <= identifiant <= fin:
                    trouvees[identifiant] = _nom_avant_separateur(suite)

        for identifiant in range(debut, fin + 1):
            nom = trouvees.get(identifiant)
            if nom:
                extensions[str(identifiant)] = {
                    "nom": nom,
                    "groupe": groupe,
                    "statut": "a_implanter",
                }

    return extensions
