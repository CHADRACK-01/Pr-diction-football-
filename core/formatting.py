# core/formatting.py
"""
Fonctions de formatage partagées (HTML Telegram).

Source unique de vérité pour la traduction des libellés de paris,
afin d'éviter les divergences entre les bulletins Free / Premium /
programme du jour / coupons.
"""


def traduire_pari(home, away, label_dc):
    """Traduit un code de pari (1X, X2, 12) en phrase positive.

    Args:
        home: nom de l'équipe à domicile.
        away: nom de l'équipe à l'extérieur.
        label_dc: code du pari ("1X", "X2", "12", ou autre).

    Returns:
        Phrase formatée en HTML, ou ``label_dc`` inchangé si inconnu.
    """
    if label_dc == "1X":
        return f"<b>{home}</b> va gagner ou faire match nul"
    if label_dc == "X2":
        return f"<b>{away}</b> va gagner ou faire match nul"
    if label_dc == "12":
        return "Un vainqueur sera désigné (pas de match nul)"
    return label_dc
