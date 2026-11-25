# core/libelles_confiance.py
"""
Libellé unique pour les probabilités du modèle.

Pas de certitude affichée (le modèle n'est pas calibré), et une seule ligne
factuelle, sans mise en garde anxiogène. Le bilan vérifiable est accessible via /bilan.
"""


def phrase_probabilite(pourcentage):
    """Phrase HTML affichée sous chaque pronostic."""
    try:
        valeur = round(float(pourcentage), 1)
    except (TypeError, ValueError):
        return ""
    return f"(Probabilité estimée : <b>{valeur}%</b> · résultats vérifiés : /bilan)"
