# core/registre.py
"""
Registre des modèles : chaque modèle porte la trace de ce qui l'a produit.

- empreinte_donnees : identifiant des matchs utilisés. Même données => même empreinte.
  Toute modification d'un seul résultat change l'empreinte.
- empreinte_modele : identifiant du modèle lui-même (sa sérialisation).
- Un modèle est reproductible si on retrouve la même empreinte de données
  et les mêmes paramètres.
"""
import hashlib
import json


def empreinte_donnees(lignes):
    """lignes : itérable de tuples (date, home, away, fthg, ftag, ftr).

    L'ordre est normalisé (tri) : seul compte l'ensemble des matchs utilisés.
    """
    normalisees = sorted(
        (str(d)[:10], str(h), str(a), int(fh), int(fa), str(r))
        for d, h, a, fh, fa, r in lignes
    )
    brut = json.dumps(normalisees, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:16]


def empreinte_modele(donnees_bundle):
    """Empreinte de la sérialisation du modèle (chaîne base64 ou bytes)."""
    if isinstance(donnees_bundle, str):
        donnees_bundle = donnees_bundle.encode("ascii")
    return hashlib.sha256(donnees_bundle).hexdigest()[:16]


def bloc_registre(lignes, parametres, versions):
    """Bloc à inscrire dans le bundle au moment de l'entraînement."""
    return {
        "empreinte_donnees": empreinte_donnees(lignes),
        "nb_matchs": len(lignes),
        "parametres": dict(parametres),
        "versions": dict(versions),
    }
