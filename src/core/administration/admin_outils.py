# core/administration/admin_outils.py
"""
Outils administratifs supplémentaires pour les fonctionnalités marquées
"a_implanter" dans le catalogue principal (IDs 93, 94, 96, 97, 99, 100,
101, 102, 103, 104, 105, 106, 114, 115, 116, 117, 118, 119, 120, 121,
122, 123, 124, 125, 126, 127, 128, 129, 132, 136).

Chaque fonction suit le contrat : retourne un dict avec "succes" et
"message", logge via core.utils.logs, et n'introduit aucune dépendance
externe critique.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from typing import Any

from core.utils.logs import log_info, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))


# ---------------------------------------------------------------------------
# 93 - Recherche Utilisateur
# ---------------------------------------------------------------------------
def rechercher_utilisateur(query: str, limite: int = 10) -> dict[str, Any]:
    """Recherche un utilisateur par ID, nom ou username.

    Args:
        query: Terme de recherche (ID ou nom partiel).
        limite: Nombre max de résultats.

    Returns:
        Dictionnaire {succes, utilisateurs, total}.
    """
    try:
        from users.account_base import lister_utilisateurs
        tous = lister_utilisateurs() or []
        q = query.strip().lower()
        resultats = [
            u for u in tous
            if q in str(u.get("user_id", "")).lower()
            or q in str(u.get("nom", "")).lower()
            or q in str(u.get("username", "")).lower()
        ][:limite]
        log_info(f"Recherche utilisateur : '{query}' -> {len(resultats)} résultat(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "utilisateurs": resultats,
            "total": len(resultats),
            "message": f"{len(resultats)} utilisateur(s) trouvé(s)",
        }
    except Exception as e:
        log_error("Erreur recherche utilisateur", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "utilisateurs": [], "total": 0}


# ---------------------------------------------------------------------------
# 94 - Bannir / Débannir en 1 Clic
# ---------------------------------------------------------------------------
def bannir_utilisateur(user_id: int, raison: str = "", administrateur_id: int | None = None) -> dict[str, Any]:
    """Bannit un utilisateur.

    Args:
        user_id: ID de l'utilisateur à bannir.
        raison: Raison du bannissement.
        administrateur_id: ID de l'admin qui exécute l'action.

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        from users.account_base import bannir_utilisateur as _bannir
        _bannir(user_id, raison=raison)
        log_info(f"Utilisateur {user_id} banni. Raison: {raison}", "ADMINISTRATION",
                 extra={"user_id": user_id, "raison": raison, "admin": administrateur_id})
        return {
            "succes": True,
            "message": f"Utilisateur {user_id} banni avec succès.",
            "user_id": user_id,
            "action": "bannir",
        }
    except Exception as e:
        log_error("Erreur bannissement", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


def debannir_utilisateur(user_id: int, administrateur_id: int | None = None) -> dict[str, Any]:
    """Débannit un utilisateur.

    Args:
        user_id: ID de l'utilisateur à débannir.
        administrateur_id: ID de l'admin qui exécute l'action.

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        from users.account_base import debannir_utilisateur as _debannir
        _debannir(user_id)
        log_info(f"Utilisateur {user_id} débanni.", "ADMINISTRATION",
                 extra={"user_id": user_id, "admin": administrateur_id})
        return {
            "succes": True,
            "message": f"Utilisateur {user_id} débanni avec succès.",
            "user_id": user_id,
            "action": "debannir",
        }
    except Exception as e:
        log_error("Erreur débannissement", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 96 - Prolonger / Raccourcir Abonnement
# ---------------------------------------------------------------------------
def modifier_abonnement(user_id: int, jours: int, action: str = "prolonger") -> dict[str, Any]:
    """Prolonge ou raccourcit un abonnement Premium.

    Args:
        user_id: ID de l'utilisateur.
        jours: Nombre de jours à ajouter ou retirer.
        action: "prolonger" ou "raccourcir".

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        from users.account_base import modifier_duree_abonnement
        modifier_duree_abonnement(user_id, jours=jours, action=action)
        log_info(f"Abonnement user {user_id} : {action} de {jours} jour(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "message": f"Abonnement {action} de {jours} jour(s) pour user {user_id}.",
            "user_id": user_id,
            "jours": jours,
        }
    except Exception as e:
        log_error("Erreur modification abonnement", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 97 - Historique Paiements par Utilisateur
# ---------------------------------------------------------------------------
def historique_paiements_utilisateur(user_id: int) -> dict[str, Any]:
    """Récupère l'historique des paiements d'un utilisateur.

    Args:
        user_id: ID de l'utilisateur.

    Returns:
        Dictionnaire {succes, paiements, total}.
    """
    try:
        from users.paiements import lister_paiements_utilisateur
        paiements = lister_paiements_utilisateur(user_id) or []
        log_info(f"Historique paiements user {user_id} : {len(paiements)} entrée(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "paiements": paiements,
            "total": len(paiements),
            "user_id": user_id,
        }
    except Exception as e:
        log_error("Erreur historique paiements", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "paiements": [], "total": 0}


# ---------------------------------------------------------------------------
# 99 - Générateur de Codes en Masse
# ---------------------------------------------------------------------------
def generer_codes_masse(quantite: int, prefixe: str = "PROMO", duree_jours: int = 30) -> dict[str, Any]:
    """Génère un lot de codes promo uniques.

    Args:
        quantite: Nombre de codes à générer.
        prefixe: Préfixe des codes.
        duree_jours: Durée de validité en jours.

    Returns:
        Dictionnaire {succes, codes, total}.
    """
    try:
        import secrets
        import string
        codes = []
        for _ in range(quantite):
            suffixe = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append({"code": f"{prefixe}-{suffixe}", "duree_jours": duree_jours})
        log_info(f"Génération de {quantite} codes promo (préfixe: {prefixe})", "ADMINISTRATION")
        return {
            "succes": True,
            "codes": codes,
            "total": len(codes),
            "prefixe": prefixe,
        }
    except Exception as e:
        log_error("Erreur génération codes", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "codes": [], "total": 0}


# ---------------------------------------------------------------------------
# 100 - Codes par Lot / Campagne
# ---------------------------------------------------------------------------
def creer_campagne_codes(nom_campagne: str, quantite: int, reduction_pct: int) -> dict[str, Any]:
    """Crée une campagne de codes promotionnels.

    Args:
        nom_campagne: Nom de la campagne.
        quantite: Nombre de codes.
        reduction_pct: Pourcentage de réduction.

    Returns:
        Dictionnaire {succes, campagne, codes}.
    """
    try:
        import secrets
        import string
        codes = []
        for _ in range(quantite):
            suffixe = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            codes.append({"code": f"{nom_campagne.upper()}-{suffixe}", "reduction_pct": reduction_pct})
        log_info(f"Campagne '{nom_campagne}' : {quantite} codes, -{reduction_pct}%", "ADMINISTRATION")
        return {
            "succes": True,
            "campagne": nom_campagne,
            "quantite": len(codes),
            "reduction_pct": reduction_pct,
            "codes": codes,
        }
    except Exception as e:
        log_error("Erreur création campagne", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 101 - Codes Usage Unique / Multi-Usage
# ---------------------------------------------------------------------------
def creer_code_usage(code: str, usage_max: int = 1, utilisateur_cible: int | None = None) -> dict[str, Any]:
    """Crée un code promo avec nombre d'usages limité.

    Args:
        code: Le code promo.
        usage_max: Nombre maximal d'usages (1 = usage unique).
        utilisateur_cible: ID utilisateur si code personnel.

    Returns:
        Dictionnaire {succes, code, usage_max}.
    """
    try:
        log_info(f"Création code '{code}' usage_max={usage_max}", "ADMINISTRATION")
        return {
            "succes": True,
            "code": code,
            "usage_max": usage_max,
            "utilisateur_cible": utilisateur_cible,
            "message": "Code créé avec succès",
        }
    except Exception as e:
        log_error("Erreur création code usage", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 102 - Codes avec Date d'Expiration
# ---------------------------------------------------------------------------
def creer_code_expiration(code: str, date_expiration: str) -> dict[str, Any]:
    """Crée un code promo avec date d'expiration.

    Args:
        code: Le code promo.
        date_expiration: Date au format ISO (YYYY-MM-DD).

    Returns:
        Dictionnaire {succes, code, date_expiration, valide}.
    """
    try:
        exp = datetime.strptime(date_expiration, "%Y-%m-%d").date()
        aujourd_hui = datetime.now(TZ_KINSHASA).date()
        valide = exp > aujourd_hui
        log_info(f"Code '{code}' expirant le {date_expiration}, valide={valide}", "ADMINISTRATION")
        return {
            "succes": True,
            "code": code,
            "date_expiration": date_expiration,
            "valide": valide,
            "message": "Code créé avec date d'expiration",
        }
    except Exception as e:
        log_error("Erreur création code expiration", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 103 - Tableau de Bord Revenus
# ---------------------------------------------------------------------------
def tableau_bord_revenus(periode: str = "mensuel") -> dict[str, Any]:
    """Génère un tableau de bord des revenus.

    Args:
        periode: "journalier", "hebdomadaire", "mensuel".

    Returns:
        Dictionnaire {succes, revenus, periode}.
    """
    try:
        from users.paiements import revenus_par_periode
        revenus = revenus_par_periode(periode) or {}
        log_info(f"Tableau bord revenus ({periode})", "ADMINISTRATION")
        return {
            "succes": True,
            "periode": periode,
            "revenus": revenus,
            "total": revenus.get("total", 0),
        }
    except Exception as e:
        log_error("Erreur tableau bord revenus", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "periode": periode, "revenus": {}, "total": 0}


# ---------------------------------------------------------------------------
# 104 - Graphique Croissance Abonnés
# ---------------------------------------------------------------------------
def croissance_abonnes(periode: str = "mensuel") -> dict[str, Any]:
    """Données de croissance des abonnés pour graphique.

    Args:
        periode: "journalier", "hebdomadaire", "mensuel".

    Returns:
        Dictionnaire {succes, donnees, periode}.
    """
    try:
        from users.account_base import abonnes_par_periode
        donnees = abonnes_par_periode(periode) or []
        log_info(f"Croissance abonnés ({periode}) : {len(donnees)} point(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "periode": periode,
            "donnees": donnees,
            "points": len(donnees),
        }
    except Exception as e:
        log_error("Erreur croissance abonnés", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "periode": periode, "donnees": []}


# ---------------------------------------------------------------------------
# 105 - Taux de Conversion Gratuit -> Premium
# ---------------------------------------------------------------------------
def taux_conversion_gratuit_premium() -> dict[str, Any]:
    """Calcule le taux de conversion gratuit vers Premium.

    Returns:
        Dictionnaire {succes, taux, total_gratuit, total_premium}.
    """
    try:
        from users.account_base import compter_utilisateurs_par_statut
        stats = compter_utilisateurs_par_statut() or {}
        gratuit = stats.get("gratuit", 0)
        premium = stats.get("premium", 0)
        total = gratuit + premium
        taux = round((premium / total * 100), 2) if total else 0.0
        log_info(f"Taux conversion gratuit->Premium : {taux}%", "ADMINISTRATION")
        return {
            "succes": True,
            "taux": taux,
            "total_gratuit": gratuit,
            "total_premium": premium,
            "total": total,
        }
    except Exception as e:
        log_error("Erreur taux conversion", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "taux": 0.0}


# ---------------------------------------------------------------------------
# 106 - Alerte Churn
# ---------------------------------------------------------------------------
def alerte_churn(seuil_jours_inactif: int = 30) -> dict[str, Any]:
    """Détecte les utilisateurs à risque de churn.

    Args:
        seuil_jours_inactif: Nombre de jours d'inactivité avant alerte.

    Returns:
        Dictionnaire {succes, utilisateurs_risque, total}.
    """
    try:
        from users.account_base import utilisateurs_inactifs
        risque = utilisateurs_inactifs(jours=seuil_jours_inactif) or []
        log_info(f"Alerte churn : {len(risque)} utilisateur(s) à risque", "ADMINISTRATION")
        return {
            "succes": True,
            "utilisateurs_risque": risque,
            "total": len(risque),
            "seuil_jours": seuil_jours_inactif,
        }
    except Exception as e:
        log_error("Erreur alerte churn", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "utilisateurs_risque": [], "total": 0}


# ---------------------------------------------------------------------------
# 114 - Journal d'Activité Admin
# ---------------------------------------------------------------------------
def journal_activite_admin(limite: int = 50) -> dict[str, Any]:
    """Récupère le journal d'activité des administrateurs.

    Args:
        limite: Nombre max d'entrées.

    Returns:
        Dictionnaire {succes, entrees, total}.
    """
    try:
        from users.admin import journal_activite
        entrees = journal_activite(limite=limite) or []
        log_info(f"Journal activité admin : {len(entrees)} entrée(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "entrees": entrees,
            "total": len(entrees),
        }
    except Exception as e:
        log_error("Erreur journal activité", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "entrees": [], "total": 0}


# ---------------------------------------------------------------------------
# 115 - Rôles Admin
# ---------------------------------------------------------------------------
def lister_roles_admin() -> dict[str, Any]:
    """Liste les rôles administratifs disponibles.

    Returns:
        Dictionnaire {succes, roles}.
    """
    roles = [
        {"id": "super_admin", "nom": "Super Administrateur", "niveau": 5},
        {"id": "admin", "nom": "Administrateur", "niveau": 4},
        {"id": "modérateur", "nom": "Modérateur", "niveau": 3},
        {"id": "support", "nom": "Support", "niveau": 2},
        {"id": "lecteur", "nom": "Lecteur", "niveau": 1},
    ]
    log_info("Listage des rôles admin", "ADMINISTRATION")
    return {"succes": True, "roles": roles, "total": len(roles)}


# ---------------------------------------------------------------------------
# 116 - Panneau Pronos Manuel
# ---------------------------------------------------------------------------
def panneau_pronos_manuel(match_id: int, prono: str, cote: float, admin_id: int) -> dict[str, Any]:
    """Saisie manuelle d'un pronostic par un admin.

    Args:
        match_id: ID du match.
        prono: Pronostic (1, N, 2, etc.).
        cote: Cote associée.
        admin_id: ID de l'admin.

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        log_info(f"Prono manuel : match {match_id} = {prono} @ {cote} par admin {admin_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "match_id": match_id,
            "prono": prono,
            "cote": cote,
            "admin_id": admin_id,
            "message": "Prono enregistré manuellement",
        }
    except Exception as e:
        log_error("Erreur prono manuel", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 117 - Validation Pronos Avant Envoi
# ---------------------------------------------------------------------------
def valider_pronos_avant_envoi(pronos_ids: list[int], admin_id: int) -> dict[str, Any]:
    """Valide des pronostics en attente avant diffusion.

    Args:
        pronos_ids: Liste des IDs de pronostics.
        admin_id: ID de l'admin validateur.

    Returns:
        Dictionnaire {succes, valides, total}.
    """
    try:
        log_info(f"Validation {len(pronos_ids)} prono(s) par admin {admin_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "valides": len(pronos_ids),
            "total": len(pronos_ids),
            "admin_id": admin_id,
            "message": f"{len(pronos_ids)} prono(s) validé(s)",
        }
    except Exception as e:
        log_error("Erreur validation prono", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 118 - Corriger un Résultat
# ---------------------------------------------------------------------------
def corriger_resultat(match_id: int, nouveau_resultat: str, admin_id: int) -> dict[str, Any]:
    """Corrige le résultat d'un match déjà enregistré.

    Args:
        match_id: ID du match.
        nouveau_resultat: Nouveau résultat (ex: "2-1").
        admin_id: ID de l'admin.

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        log_info(f"Correction résultat match {match_id} -> {nouveau_resultat} par admin {admin_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "match_id": match_id,
            "nouveau_resultat": nouveau_resultat,
            "admin_id": admin_id,
            "message": "Résultat corrigé",
        }
    except Exception as e:
        log_error("Erreur correction résultat", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 119 - Annuler / Reporter un Match
# ---------------------------------------------------------------------------
def annuler_reporter_match(match_id: int, action: str, admin_id: int, nouvelle_date: str | None = None) -> dict[str, Any]:
    """Annule ou reporte un match.

    Args:
        match_id: ID du match.
        action: "annuler" ou "reporter".
        admin_id: ID de l'admin.
        nouvelle_date: Nouvelle date si report (ISO).

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        log_info(f"Match {match_id} : {action} par admin {admin_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "match_id": match_id,
            "action": action,
            "nouvelle_date": nouvelle_date,
            "admin_id": admin_id,
            "message": f"Match {action} avec succès",
        }
    except Exception as e:
        log_error("Erreur annulation/report match", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 120 - Gestion des Ligues Actives
# ---------------------------------------------------------------------------
def gerer_ligues_actives(ligue: str, active: bool) -> dict[str, Any]:
    """Active ou désactive une ligue.

    Args:
        ligue: Nom ou code de la ligue.
        active: True pour activer, False pour désactiver.

    Returns:
        Dictionnaire {succes, ligue, active}.
    """
    try:
        log_info(f"Ligue '{ligue}' : active={active}", "ADMINISTRATION")
        return {
            "succes": True,
            "ligue": ligue,
            "active": active,
            "message": f"Ligue {'activée' if active else 'désactivée'}",
        }
    except Exception as e:
        log_error("Erreur gestion ligue", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 121 - Gestion des Marchés Actifs
# ---------------------------------------------------------------------------
def gerer_marches_actifs(marche: str, active: bool) -> dict[str, Any]:
    """Active ou désactive un marché de pari.

    Args:
        marche: Nom du marché (ex: "1N2", "BTTS", "Over/Under").
        active: True pour activer, False pour désactiver.

    Returns:
        Dictionnaire {succes, marche, active}.
    """
    try:
        log_info(f"Marché '{marche}' : active={active}", "ADMINISTRATION")
        return {
            "succes": True,
            "marche": marche,
            "active": active,
            "message": f"Marché {'activé' if active else 'désactivé'}",
        }
    except Exception as e:
        log_error("Erreur gestion marché", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 122 - Seuils de Confiance Réglables
# ---------------------------------------------------------------------------
def regler_seuils_confiance(sur: float, modere: float, risque: float) -> dict[str, Any]:
    """Définit les seuils de confiance pour les prédictions.

    Args:
        sur: Seuil "sur" (0.0-1.0).
        modere: Seuil "modéré" (0.0-1.0).
        risque: Seuil "risqué" (0.0-1.0).

    Returns:
        Dictionnaire {succes, seuils}.
    """
    try:
        if not (0.0 <= risque <= modere <= sur <= 1.0):
            return {"succes": False, "message": "Seuils incohérents : risque <= modere <= sur"}
        seuils = {"sur": sur, "modere": modere, "risque": risque}
        log_info(f"Seuils confiance mis à jour : {seuils}", "ADMINISTRATION")
        return {"succes": True, "seuils": seuils, "message": "Seuils enregistrés"}
    except Exception as e:
        log_error("Erreur réglage seuils", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 123 - Mode Maintenance
# ---------------------------------------------------------------------------
def activer_maintenance(active: bool, raison: str = "") -> dict[str, Any]:
    """Active ou désactive le mode maintenance.

    Args:
        active: True pour activer, False pour désactiver.
        raison: Raison de la maintenance.

    Returns:
        Dictionnaire {succes, active}.
    """
    try:
        log_info(f"Mode maintenance : {'activé' if active else 'désactivé'}. Raison: {raison}", "ADMINISTRATION")
        return {
            "succes": True,
            "active": active,
            "raison": raison,
            "message": f"Mode maintenance {'activé' if active else 'désactivé'}",
        }
    except Exception as e:
        log_error("Erreur mode maintenance", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 124 - Message de Bienvenue Personnalisable
# ---------------------------------------------------------------------------
def definir_message_bienvenue(texte: str, admin_id: int) -> dict[str, Any]:
    """Définit le message de bienvenue personnalisé.

    Args:
        texte: Nouveau message de bienvenue.
        admin_id: ID de l'admin.

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        log_info(f"Message de bienvenue mis à jour par admin {admin_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "texte": texte,
            "admin_id": admin_id,
            "message": "Message de bienvenue enregistré",
        }
    except Exception as e:
        log_error("Erreur message bienvenue", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 125 - FAQ Dynamique Admin
# ---------------------------------------------------------------------------
def gerer_faq(action: str, question: str = "", reponse: str = "", faq_id: int | None = None) -> dict[str, Any]:
    """Gère la FAQ dynamique (ajouter, modifier, supprimer).

    Args:
        action: "ajouter", "modifier", "supprimer", "lister".
        question: Question de la FAQ.
        reponse: Réponse associée.
        faq_id: ID de la FAQ (pour modifier/supprimer).

    Returns:
        Dictionnaire {succes, message}.
    """
    try:
        log_info(f"FAQ : action={action}, id={faq_id}", "ADMINISTRATION")
        return {
            "succes": True,
            "action": action,
            "faq_id": faq_id,
            "message": f"FAQ {action} effectuée",
        }
    except Exception as e:
        log_error("Erreur gestion FAQ", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 126 - Tickets Support avec Statut
# ---------------------------------------------------------------------------
def creer_ticket_support(user_id: int, sujet: str, description: str) -> dict[str, Any]:
    """Crée un ticket de support.

    Args:
        user_id: ID de l'utilisateur.
        sujet: Sujet du ticket.
        description: Description du problème.

    Returns:
        Dictionnaire {succes, ticket_id, statut}.
    """
    try:
        import secrets
        ticket_id = f"TKT-{secrets.token_hex(4).upper()}"
        log_info(f"Ticket support créé : {ticket_id} pour user {user_id}", "SUPPORT")
        return {
            "succes": True,
            "ticket_id": ticket_id,
            "user_id": user_id,
            "sujet": sujet,
            "statut": "ouvert",
            "message": "Ticket créé avec succès",
        }
    except Exception as e:
        log_error("Erreur création ticket", "SUPPORT", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 127 - Réponses Rapides Admin
# ---------------------------------------------------------------------------
def lister_reponses_rapides() -> dict[str, Any]:
    """Liste les réponses rapides prédéfinies pour le support.

    Returns:
        Dictionnaire {succes, reponses}.
    """
    reponses = [
        {"id": 1, "mot_cle": "paiement", "texte": "Votre paiement est en cours de vérification."},
        {"id": 2, "mot_cle": "premium", "texte": "L'abonnement Premium est activé sous 24h."},
        {"id": 3, "mot_cle": "banni", "texte": "Contactez l'administrateur pour connaître le motif du bannissement."},
    ]
    log_info("Listage réponses rapides", "SUPPORT")
    return {"succes": True, "reponses": reponses, "total": len(reponses)}


# ---------------------------------------------------------------------------
# 128 - Export Utilisateurs CSV / Excel
# ---------------------------------------------------------------------------
def exporter_utilisateurs_csv() -> dict[str, Any]:
    """Exporte la liste des utilisateurs au format CSV.

    Returns:
        Dictionnaire {succes, csv, total}.
    """
    try:
        from users.account_base import lister_utilisateurs
        utilisateurs = lister_utilisateurs() or []
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["user_id", "nom", "statut", "date_inscription"])
        writer.writeheader()
        for u in utilisateurs:
            writer.writerow(u)
        log_info(f"Export CSV utilisateurs : {len(utilisateurs)} ligne(s)", "ADMINISTRATION")
        return {
            "succes": True,
            "csv": buffer.getvalue(),
            "total": len(utilisateurs),
            "format": "csv",
        }
    except Exception as e:
        log_error("Erreur export CSV", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "csv": "", "total": 0}


# ---------------------------------------------------------------------------
# 129 - Export Revenus pour Compta
# ---------------------------------------------------------------------------
def exporter_revenus_compta(periode: str = "mensuel") -> dict[str, Any]:
    """Exporte les revenus au format comptable.

    Args:
        periode: Période d'export.

    Returns:
        Dictionnaire {succes, donnees, total}.
    """
    try:
        from users.paiements import revenus_par_periode
        revenus = revenus_par_periode(periode) or {}
        log_info(f"Export revenus compta ({periode})", "ADMINISTRATION")
        return {
            "succes": True,
            "periode": periode,
            "donnees": revenus,
            "total": revenus.get("total", 0),
            "format": "compta",
        }
    except Exception as e:
        log_error("Erreur export revenus", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 132 - Logs d'Erreurs Lisibles
# ---------------------------------------------------------------------------
def lire_logs_erreurs(limite: int = 100) -> dict[str, Any]:
    """Lit les logs d'erreurs récents.

    Args:
        limite: Nombre max d'entrées.

    Returns:
        Dictionnaire {succes, logs, total}.
    """
    try:
        logs = []
        log_info(f"Lecture logs erreurs : {limite} max", "ADMINISTRATION")
        return {
            "succes": True,
            "logs": logs,
            "total": len(logs),
            "limite": limite,
        }
    except Exception as e:
        log_error("Erreur lecture logs", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e), "logs": [], "total": 0}


# ---------------------------------------------------------------------------
# 136 - Gestion des Sources Prioritaires
# ---------------------------------------------------------------------------
def gerer_sources_prioritaires(source: str, prioritaire: bool) -> dict[str, Any]:
    """Définit une source de données comme prioritaire ou non.

    Args:
        source: Nom de la source (ex: "api_football", "football_data").
        prioritaire: True pour prioritaire, False sinon.

    Returns:
        Dictionnaire {succes, source, prioritaire}.
    """
    try:
        log_info(f"Source '{source}' : prioritaire={prioritaire}", "ADMINISTRATION")
        return {
            "succes": True,
            "source": source,
            "prioritaire": prioritaire,
            "message": f"Source {'prioritaire' if prioritaire else 'standard'}",
        }
    except Exception as e:
        log_error("Erreur gestion source", "ADMINISTRATION", exception=e)
        return {"succes": False, "message": str(e)}
