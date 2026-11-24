# core/bankroll.py
"""
Fonctionnalités 41 & 42 : Gestion de Bankroll.
Calcule la mise idéale selon la méthode Kelly ou une mise fixe.
"""

from users.database import db_execute, db_fetchone
from core.utils.logs import log_info, log_error


def _assurer_table_bankroll():
    """Crée la table bankroll si elle n'existe pas."""
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS bankroll (
            user_id INTEGER PRIMARY KEY,
            montant_total REAL DEFAULT 0,
            strategie TEXT DEFAULT 'kelly_fractionne',
            pourcentage_mise REAL DEFAULT 2.0
        )
        """,
        db_context={"table": "bankroll", "operation": "create"}
    )


def set_bankroll(user_id, montant_total, strategie="kelly_fractionne", pourcentage_mise=2.0):
    """Définit la bankroll d'un utilisateur."""
    _assurer_table_bankroll()

    rowcount = db_execute(
        """
        INSERT INTO bankroll (user_id, montant_total, strategie, pourcentage_mise)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id) DO UPDATE SET
            montant_total = excluded.montant_total,
            strategie = excluded.strategie,
            pourcentage_mise = excluded.pourcentage_mise
        """,
        params=[user_id, montant_total, strategie, pourcentage_mise],
        db_context={"table": "bankroll", "operation": "set"}
    )

    if rowcount is None:
        return False
    log_info(f"Bankroll mise à jour pour {user_id} : {montant_total} ({strategie})", "BANKROLL")
    return True


def get_bankroll(user_id):
    """Récupère la bankroll d'un utilisateur."""
    _assurer_table_bankroll()

    row = db_fetchone(
        "SELECT montant_total, strategie, pourcentage_mise FROM bankroll WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "bankroll", "operation": "get"}
    )

    if not row:
        return None

    return {
        "montant_total": row[0],
        "strategie": row[1],
        "pourcentage_mise": row[2]
    }


def calculer_mise(user_id, proba_ia, cote):
    """
    Calcule la mise idéale selon la stratégie de l'utilisateur.
    - kelly_fractionne : Kelly divisé par 4 (prudent)
    - fixe : pourcentage fixe de la bankroll
    - martingale_douce : (à implémenter plus tard)
    """
    bankroll = get_bankroll(user_id)
    if not bankroll or bankroll["montant_total"] <= 0:
        return None, "❌ Tu n'as pas encore défini ta bankroll."

    montant = bankroll["montant_total"]
    strategie = bankroll["strategie"]

    if strategie == "fixe":
        mise = montant * (bankroll["pourcentage_mise"] / 100)
        return round(mise, 0), f"Mise fixe ({bankroll['pourcentage_mise']}% de ta bankroll)"

    elif strategie == "kelly_fractionne":
        # Formule de Kelly : f* = (bp - q) / b
        # b = cote - 1, p = proba, q = 1 - p
        if cote <= 1.0:
            return 0, "Cote invalide."

        b = cote - 1
        p = proba_ia
        q = 1 - p
        kelly = (b * p - q) / b

        if kelly <= 0:
            return 0, "Pas de value bet détecté selon la méthode Kelly."

        # Kelly fractionné (divisé par 4 pour être prudent)
        kelly_prudent = kelly / 4
        mise = montant * kelly_prudent

        return round(mise, 0), f"Méthode Kelly fractionnée ({round(kelly_prudent * 100, 2)}% de ta bankroll)"

    else:
        return 0, "Stratégie inconnue."


def formater_bankroll(bankroll, mise, explication):
    """Formate le résultat pour Telegram."""
    if not bankroll:
        return "❌ Tu n'as pas encore défini ta bankroll. Utilise /bankroll MONTANT"

    texte = f"💰 <b>GESTION DE BANKROLL</b>\n"
    texte += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    texte += f"💵 Bankroll totale : {bankroll['montant_total']:,.0f} CDF\n"
    texte += f"📊 Stratégie : {bankroll['strategie']}\n\n"

    if mise > 0:
        texte += f"🎯 <b>Mise conseillée : {mise:,.0f} CDF</b>\n"
        texte += f"📝 {explication}\n\n"
        texte += f"💡 <i>Ne mise jamais plus de 5% de ta bankroll sur un seul pari.</i>"
    else:
        texte += f"⚠️ {explication}"

    return texte
