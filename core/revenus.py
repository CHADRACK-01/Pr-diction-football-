# core/revenus.py
"""
Tableau de bord des revenus (fonctionnalités 103 et 129).

Lecture seule : ne modifie jamais la base.
Source : paiements_attente, statut = 'valide', montant en CDF.

Les erreurs de base ne sont PAS avalées : une erreur remonte à l'appelant,
pour éviter d'afficher un revenu de 0 faux à l'administrateur.
"""

import csv
import io
from datetime import date


_REQUETE_PAR_JOUR = """
    SELECT substr(date_validation, 1, 10) AS jour,
           COUNT(*) AS nb,
           COALESCE(SUM(montant), 0) AS total
    FROM paiements_attente
    WHERE statut = 'valide'
      AND date(date_validation) >= date(?)
      AND date(date_validation) <= date(?)
    GROUP BY jour
    ORDER BY jour
"""


def _connexion(conn=None):
    if conn is not None:
        return conn, False
    from users.db import get_connection
    return get_connection(), True


def _valider_periode(debut, fin):
    if not isinstance(debut, date) or not isinstance(fin, date):
        raise TypeError("debut et fin doivent être des objets date")
    if debut > fin:
        raise ValueError("la date de début est après la date de fin")


def revenus_par_jour(debut, fin, conn=None):
    """Retourne une liste de dicts {jour, nb_paiements, total_cdf} entre debut et fin (inclus)."""
    _valider_periode(debut, fin)
    cnx, a_fermer = _connexion(conn)
    try:
        rows = cnx.execute(_REQUETE_PAR_JOUR, (debut.isoformat(), fin.isoformat())).fetchall()
    finally:
        if a_fermer:
            cnx.close()
    return [
        {"jour": jour, "nb_paiements": nb, "total_cdf": int(total)}
        for jour, nb, total in rows
    ]


def total_revenus(debut, fin, conn=None):
    """Retourne (nb_paiements, total_cdf) sur la période."""
    details = revenus_par_jour(debut, fin, conn=conn)
    return (
        sum(d["nb_paiements"] for d in details),
        sum(d["total_cdf"] for d in details),
    )


def exporter_revenus_csv(debut, fin, conn=None):
    """Retourne le CSV (texte) des revenus journaliers, pour la comptabilité (fonctionnalité 129)."""
    details = revenus_par_jour(debut, fin, conn=conn)
    tampon = io.StringIO()
    writer = csv.writer(tampon, delimiter=";")
    writer.writerow(["jour", "nb_paiements", "total_cdf"])
    for d in details:
        writer.writerow([d["jour"], d["nb_paiements"], d["total_cdf"]])
    return tampon.getvalue()
