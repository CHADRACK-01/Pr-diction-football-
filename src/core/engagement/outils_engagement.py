# core/engagement/outils_engagement.py
"""
Outils d'engagement utilisateur pour les fonctionnalités marquées
"a_implanter" dans le catalogue principal (IDs 12, 13, 34, 36, 67, 68,
69).

Contrat : retourne un dict avec "succes", logge via core.utils.logs,
aucune dépendance externe critique.
"""

from __future__ import annotations

from typing import Any
import secrets

from core.utils.logs import log_info, log_error


# ---------------------------------------------------------------------------
# 12 - Quiz / Sondage Avant Match
# ---------------------------------------------------------------------------
def creer_quiz_avant_match(match_id: int, question: str, options: list[str]) -> dict[str, Any]:
    """Crée un quiz ou sondage avant un match.

    Args:
        match_id: ID du match.
        question: Question du quiz.
        options: Liste des options de réponse.

    Returns:
        Dictionnaire {succes, quiz_id, question, options}.
    """
    try:
        quiz_id = f"QUIZ-{secrets.token_hex(4).upper()}"
        log_info(f"Quiz créé : {quiz_id} pour match {match_id}", "ENGAGEMENT")
        return {
            "succes": True,
            "quiz_id": quiz_id,
            "match_id": match_id,
            "question": question,
            "options": options,
            "message": "Quiz créé avec succès",
        }
    except Exception as e:
        log_error("Erreur création quiz", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 13 - Mode Sans Internet / SMS Résumé
# ---------------------------------------------------------------------------
def generer_resume_sms(pronos: list[dict[str, Any]]) -> dict[str, Any]:
    """Génère un résumé au format SMS pour mode hors ligne.

    Args:
        pronos: Liste des pronostics {match, conseil}.

    Returns:
        Dictionnaire {succes, resume, longueur}.
    """
    try:
        lignes = [f"• {p.get('match', '')}: {p.get('conseil', '')}" for p in pronos]
        resume = "PRONOS DU JOUR\n" + "\n".join(lignes)
        log_info(f"Résumé SMS généré : {len(pronos)} pronos", "EXPÉRIENCE")
        return {
            "succes": True,
            "resume": resume,
            "longueur": len(resume),
            "nb_pronos": len(pronos),
            "message": "Résumé SMS généré",
        }
    except Exception as e:
        log_error("Erreur génération SMS", "EXPÉRIENCE", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 34 - Classement par Quartier / Ville
# ---------------------------------------------------------------------------
def classement_par_ville(utilisateurs: list[dict[str, Any]]) -> dict[str, Any]:
    """Classe les utilisateurs par ville/quartier selon leurs gains.

    Args:
        utilisateurs: Liste des utilisateurs avec ville et gains.

    Returns:
        Dictionnaire {succes, classements, total_villes}.
    """
    try:
        par_ville: dict[str, list[dict[str, Any]]] = {}
        for u in utilisateurs:
            ville = u.get("ville", "Inconnue")
            par_ville.setdefault(ville, []).append(u)
        classements = {}
        for ville, users in par_ville.items():
            trie = sorted(users, key=lambda x: x.get("gains", 0), reverse=True)
            classements[ville] = trie[:5]
        log_info(f"Classement par ville : {len(par_ville)} ville(s)", "ENGAGEMENT")
        return {
            "succes": True,
            "classements": classements,
            "total_villes": len(par_ville),
            "message": "Classement généré",
        }
    except Exception as e:
        log_error("Erreur classement ville", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e), "classements": {}, "total_villes": 0}


# ---------------------------------------------------------------------------
# 36 - Mode Duo / Pari à 2
# ---------------------------------------------------------------------------
def creer_pari_duo(user_id_1: int, user_id_2: int, match_id: int, prono: str) -> dict[str, Any]:
    """Crée un pari en duo entre deux utilisateurs.

    Args:
        user_id_1: ID du premier utilisateur.
        user_id_2: ID du second utilisateur.
        match_id: ID du match.
        prono: Pronostic choisi.

    Returns:
        Dictionnaire {succes, duo_id, statut}.
    """
    try:
        duo_id = f"DUO-{secrets.token_hex(4).upper()}"
        log_info(f"Pari duo créé : {duo_id} entre {user_id_1} et {user_id_2}", "ENGAGEMENT")
        return {
            "succes": True,
            "duo_id": duo_id,
            "user_id_1": user_id_1,
            "user_id_2": user_id_2,
            "match_id": match_id,
            "prono": prono,
            "statut": "en_attente",
            "message": "Pari duo créé",
        }
    except Exception as e:
        log_error("Erreur création pari duo", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 67 - Paris Virtuels Argent Fictif
# ---------------------------------------------------------------------------
def creer_pari_virtuel(user_id: int, match_id: int, prono: str, mise_fictive: float) -> dict[str, Any]:
    """Enregistre un pari avec argent fictif.

    Args:
        user_id: ID de l'utilisateur.
        match_id: ID du match.
        prono: Pronostic.
        mise_fictive: Montant fictif misé.

    Returns:
        Dictionnaire {succes, pari_id, solde_fictif}.
    """
    try:
        pari_id = f"VIRT-{secrets.token_hex(4).upper()}"
        log_info(f"Pari virtuel : {pari_id} user {user_id} mise {mise_fictive}", "ENGAGEMENT")
        return {
            "succes": True,
            "pari_id": pari_id,
            "user_id": user_id,
            "match_id": match_id,
            "prono": prono,
            "mise_fictive": mise_fictive,
            "statut": "en_cours",
            "message": "Pari virtuel enregistré",
        }
    except Exception as e:
        log_error("Erreur pari virtuel", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 68 - Ligue Privée Entre Amis
# ---------------------------------------------------------------------------
def creer_ligue_privee(nom: str, createur_id: int, amis_ids: list[int]) -> dict[str, Any]:
    """Crée une ligue privée entre amis.

    Args:
        nom: Nom de la ligue.
        createur_id: ID du créateur.
        amis_ids: Liste des IDs d'amis invités.

    Returns:
        Dictionnaire {succes, ligue_id, membres}.
    """
    try:
        ligue_id = f"LIGUE-{secrets.token_hex(4).upper()}"
        membres = [createur_id] + amis_ids
        log_info(f"Ligue privée créée : {ligue_id} ({len(membres)} membres)", "ENGAGEMENT")
        return {
            "succes": True,
            "ligue_id": ligue_id,
            "nom": nom,
            "createur_id": createur_id,
            "membres": membres,
            "total_membres": len(membres),
            "message": "Ligue privée créée",
        }
    except Exception as e:
        log_error("Erreur création ligue", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 69 - Bataille IA vs Humains
# ---------------------------------------------------------------------------
def lancer_bataille_ia_vs_humains(match_id: int, prono_ia: str, pronos_humains: list[str]) -> dict[str, Any]:
    """Lance une bataille de pronostics IA vs humains.

    Args:
        match_id: ID du match.
        prono_ia: Pronostic de l'IA.
        pronos_humains: Liste des pronostics humains.

    Returns:
        Dictionnaire {succes, battle_id, resultat_ia, gagnants}.
    """
    try:
        battle_id = f"BATTLE-{secrets.token_hex(4).upper()}"
        gagnants = [p for p in pronos_humains if p == prono_ia]
        log_info(f"Bataille IA vs humains : {battle_id}, IA={prono_ia}", "ENGAGEMENT")
        return {
            "succes": True,
            "battle_id": battle_id,
            "match_id": match_id,
            "prono_ia": prono_ia,
            "pronostics_humains": pronos_humains,
            "gagnants_contre_ia": gagnants,
            "message": "Bataille lancée",
        }
    except Exception as e:
        log_error("Erreur bataille IA", "ENGAGEMENT", exception=e)
        return {"succes": False, "message": str(e)}
