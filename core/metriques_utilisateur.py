"""Métriques locales pour ROI, croissance, conversion et churn."""

from datetime import datetime, timedelta

from users.db import db_fetchall


def calculer_roi_personnel(user_id):
    rows = db_fetchall(
        "SELECT montant_mise, montant_retour FROM historiques_paris WHERE user_id = ?",
        params=[user_id],
        db_context={"table": "historiques_paris", "operation": "roi"},
    )
    mises = sum(float(row[0] or 0) for row in rows)
    retours = sum(float(row[1] or 0) for row in rows)
    benefice = retours - mises
    roi = (benefice / mises * 100) if mises > 0 else 0.0
    return {"mises": mises, "retours": retours, "benefice": benefice, "roi_pourcent": round(roi, 2)}


def calculer_croissance_abonnes():
    rows = db_fetchall(
        "SELECT status, COUNT(*) FROM utilisateurs GROUP BY status",
        db_context={"table": "utilisateurs", "operation": "growth"},
    )
    comptes = {row[0] or "free": int(row[1]) for row in rows}
    return {
        "nouveaux": 0,
        "actifs": comptes.get("premium", 0) + comptes.get("vip", 0),
        "premium": comptes.get("premium", 0),
        "free": comptes.get("free", 0),
        "churn": comptes.get("expire", 0),
    }


def calculer_conversion_premium():
    rows = db_fetchall(
        "SELECT status, COUNT(*) FROM utilisateurs GROUP BY status",
        db_context={"table": "utilisateurs", "operation": "conversion"},
    )
    comptes = {row[0] or "free": int(row[1]) for row in rows}
    gratuits = comptes.get("free", 0)
    premiums = comptes.get("premium", 0)
    base = gratuits + premiums
    taux = (premiums / base * 100) if base > 0 else 0.0
    return {"gratuit": gratuits, "premium": premiums, "taux_conversion_pourcent": round(taux, 2)}


def detecter_churn(jours_avant_expiration=1):
    limite = datetime.now() + timedelta(days=jours_avant_expiration)
    rows = db_fetchall(
        "SELECT user_id, date_expiration FROM utilisateurs "
        "WHERE status = 'premium' AND date_expiration IS NOT NULL "
        "AND date_expiration <= ?",
        params=[limite.strftime("%Y-%m-%d %H:%M:%S")],
        db_context={"table": "utilisateurs", "operation": "churn"},
    )
    return [{"user_id": row[0], "date_expiration": row[1]} for row in rows]
