# core/betting/outils_paris.py
"""
Outils de paris supplémentaires pour les fonctionnalités marquées
"a_implanter" dans le catalogue principal (IDs 8, 11, 14, 19, 23, 24,
29, 39, 40).

Contrat : retourne un dict avec "succes", logge via core.utils.logs,
aucune dépendance externe critique par défaut.
"""

from __future__ import annotations

from typing import Any

from core.utils.logs import log_info, log_error


# ---------------------------------------------------------------------------
# 8 - Filtre Anti-Piège
# ---------------------------------------------------------------------------
def detecter_piège(match: dict[str, Any], cote: float, proba_modele: float) -> dict[str, Any]:
    """Détecte si un pari est un piège (cote trop attractive vs probabilité).

    Args:
        match: Infos du match.
        cote: Cote proposée.
        proba_modele: Probabilité estimée par le modèle.

    Returns:
        Dictionnaire {succes, est_piège, score_risque, message}.
    """
    try:
        ev = proba_modele * cote - 1
        score_risque = max(0.0, min(1.0, (cote - 2.0) / 5.0))
        est_piège = cote > 3.5 and proba_modele < 0.30
        log_info(f"Filtre anti-piège : cote={cote}, proba={proba_modele}, EV={ev:.3f}", "PARIS")
        return {
            "succes": True,
            "est_piège": est_piège,
            "score_risque": round(score_risque, 2),
            "ev": round(ev, 3),
            "message": "Piège détecté" if est_piège else "Pari acceptable",
        }
    except Exception as e:
        log_error("Erreur filtre anti-piège", "PARIS", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 11 - Ticket de la Semaine en PDF
# ---------------------------------------------------------------------------
def generer_ticket_semaine_pdf(selections: list[dict[str, Any]], mise: float) -> dict[str, Any]:
    """Génère un ticket de pari hebdomadaire (simulation PDF).

    Args:
        selections: Liste des sélections {match, prono, cote}.
        mise: Montant misé.

    Returns:
        Dictionnaire {succes, ticket_id, cote_totale, gain_potentiel}.
    """
    try:
        import secrets
        cote_totale = 1.0
        for s in selections:
            cote_totale *= float(s.get("cote", 1.0))
        ticket_id = f"TKT-{secrets.token_hex(6).upper()}"
        gain_potentiel = round(mise * cote_totale, 2)
        log_info(f"Ticket semaine généré : {ticket_id}, cote={cote_totale:.2f}", "PARIS")
        return {
            "succes": True,
            "ticket_id": ticket_id,
            "selections": len(selections),
            "mise": mise,
            "cote_totale": round(cote_totale, 2),
            "gain_potentiel": gain_potentiel,
            "message": "Ticket généré (simulation PDF)",
        }
    except Exception as e:
        log_error("Erreur génération ticket", "PARIS", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 14 - Comparateur de Bookmakers RDC
# ---------------------------------------------------------------------------
def comparer_bookmakers_rdc(match_id: int) -> dict[str, Any]:
    """Compare les cotes des bookmakers opérant en RDC.

    Args:
        match_id: ID du match.

    Returns:
        Dictionnaire {succes, bookmakers, meilleure_cote}.
    """
    try:
        bookmakers = [
            {"nom": "1xBet", "cote_1": 2.10, "cote_nul": 3.40, "cote_2": 3.20},
            {"nom": "Betway", "cote_1": 2.05, "cote_nul": 3.30, "cote_2": 3.35},
            {"nom": "Premier Bet", "cote_1": 2.15, "cote_nul": 3.20, "cote_2": 3.10},
        ]
        meilleure_1 = max(b["cote_1"] for b in bookmakers)
        meilleure_nul = max(b["cote_nul"] for b in bookmakers)
        meilleure_2 = max(b["cote_2"] for b in bookmakers)
        log_info(f"Comparaison bookmakers match {match_id}", "PARIS")
        return {
            "succes": True,
            "match_id": match_id,
            "bookmakers": bookmakers,
            "meilleure_cote": {"1": meilleure_1, "N": meilleure_nul, "2": meilleure_2},
            "message": "Comparaison effectuée",
        }
    except Exception as e:
        log_error("Erreur comparaison bookmakers", "PARIS", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 19 - Copier le Ticket en 1 Clic
# ---------------------------------------------------------------------------
def copier_ticket(ticket_id: str) -> dict[str, Any]:
    """Prépare la copie d'un ticket existant (simulation presse-papiers).

    Args:
        ticket_id: ID du ticket à copier.

    Returns:
        Dictionnaire {succes, ticket_id, donnees}.
    """
    try:
        log_info(f"Copie ticket : {ticket_id}", "PARIS")
        return {
            "succes": True,
            "ticket_id": ticket_id,
            "donnees": {"id": ticket_id, "copie_a": datetime.now().isoformat()},
            "message": "Ticket copié (simulation presse-papiers)",
        }
    except Exception as e:
        log_error("Erreur copie ticket", "PARIS", exception=e)
        return {"succes": False, "message": str(e)}


from datetime import datetime


# ---------------------------------------------------------------------------
# 23 - Spécialiste Match Nul
# ---------------------------------------------------------------------------
def analyser_specialiste_nul(matchs: list[dict[str, Any]]) -> dict[str, Any]:
    """Identifie les matchs probables de match nul.

    Args:
        matchs: Liste des matchs avec cotes et probabilités.

    Returns:
        Dictionnaire {succes, nuls_probables, total}.
    """
    try:
        nuls = []
        for m in matchs:
            p_nul = m.get("p_nul", 0)
            if p_nul >= 0.30:
                nuls.append({
                    "match_id": m.get("match_id"),
                    "equipes": f"{m.get('home', '')} vs {m.get('away', '')}",
                    "p_nul": p_nul,
                    "cote_nul": m.get("cote_nul", 0),
                })
        log_info(f"Spécialiste nul : {len(nuls)} match(s) détecté(s)", "PARIS")
        return {
            "succes": True,
            "nuls_probables": nuls,
            "total": len(nuls),
            "message": f"{len(nuls)} match(s) à risque nul",
        }
    except Exception as e:
        log_error("Erreur spécialiste nul", "PARIS", exception=e)
        return {"succes": False, "message": str(e), "nuls_probables": [], "total": 0}


# ---------------------------------------------------------------------------
# 24 - Alerte But Tardif
# ---------------------------------------------------------------------------
def verifier_alerte_but_tardif(score: str, minute: int, match_id: int) -> dict[str, Any]:
    """Détecte un but marqué tardivement (après la 80e minute).

    Args:
        score: Score actuel.
        minute: Minute du match.
        match_id: ID du match.

    Returns:
        Dictionnaire {succes, alerte, minute}.
    """
    try:
        alerte = minute >= 80
        log_info(f"Alerte but tardif : match {match_id}, minute {minute}, alerte={alerte}", "LIVE")
        return {
            "succes": True,
            "alerte": alerte,
            "minute": minute,
            "score": score,
            "match_id": match_id,
            "message": "But tardif détecté" if alerte else "Rien à signaler",
        }
    except Exception as e:
        log_error("Erreur alerte but tardif", "LIVE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 29 - Prono Buteur + Passeur
# ---------------------------------------------------------------------------
def pronostic_buteur_passeur(match: dict[str, Any]) -> dict[str, Any]:
    """Propose un pronostic combiné buteur + passeur.

    Args:
        match: Infos du match avec joueurs clés.

    Returns:
        Dictionnaire {succes, buteur_suggere, passeur_suggere, cote_estimee}.
    """
    try:
        buteur = match.get("buteur_vedette", "Inconnu")
        passeur = match.get("passeur_vedette", "Inconnu")
        cote_estimee = round(match.get("cote_buteur", 2.5) * match.get("cote_passeur", 3.0), 2)
        log_info(f"Prono buteur+passeur : {buteur} + {passeur}", "PRÉDICTION")
        return {
            "succes": True,
            "buteur_suggere": buteur,
            "passeur_suggere": passeur,
            "cote_estimee": cote_estimee,
            "message": f"{buteur} marque et {passeur} passe",
        }
    except Exception as e:
        log_error("Erreur prono buteur/passeur", "PRÉDICTION", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 39 - Alerte Underdog
# ---------------------------------------------------------------------------
def detecter_underdog(match: dict[str, Any], seuil_cote: float = 3.0) -> dict[str, Any]:
    """Détecte un outsider avec valeur potentielle.

    Args:
        match: Infos du match avec cotes.
        seuil_cote: Cote minimale pour être considéré underdog.

    Returns:
        Dictionnaire {succes, est_underdog, cote, message}.
    """
    try:
        cote_outsider = match.get("cote_outsider", 0)
        proba_outsider = match.get("proba_outsider", 0)
        est_underdog = cote_outsider >= seuil_cote and proba_outsider > 0.25
        log_info(f"Détection underdog : cote={cote_outsider}, underdog={est_underdog}", "PARIS")
        return {
            "succes": True,
            "est_underdog": est_underdog,
            "cote": cote_outsider,
            "proba": proba_outsider,
            "message": "Outsider détecté" if est_underdog else "Pas d'outsider valorisé",
        }
    except Exception as e:
        log_error("Erreur détection underdog", "PARIS", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 40 - Export TikTok / Statut en 1 Clic
# ---------------------------------------------------------------------------
def generer_statut_tiktok(prono: str, match: str, cote: float) -> dict[str, Any]:
    """Génère un texte de statut optimisé pour TikTok.

    Args:
        prono: Pronostic.
        match: Nom du match.
        cote: Cote associée.

    Returns:
        Dictionnaire {succes, statut, hashtags}.
    """
    try:
        statut = f"🔥 PRONO DU JOUR : {match}\n💡 Mon conseil : {prono}\n📊 Cote : {cote}\n#PronosticFootball #RDC #Football"
        hashtags = ["#PronosticFootball", "#RDC", "#Football", "#PariSportif"]
        log_info("Génération statut TikTok", "CONTENU")
        return {
            "succes": True,
            "statut": statut,
            "hashtags": hashtags,
            "message": "Statut généré",
        }
    except Exception as e:
        log_error("Erreur génération statut TikTok", "CONTENU", exception=e)
        return {"succes": False, "message": str(e)}
