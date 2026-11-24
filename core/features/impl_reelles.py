# core/features/impl_reelles.py
"""
Implémentations RÉELLES (non stubs) des fonctionnalités sans dépendance externe.

Toutes les fonctions de ce module sont utilisables en l'état. Elles n'ont
besoin d'aucune API externe, d'aucune clé, d'aucun service tiers.
Certaines utilisent la base de données Turso si disponible, sinon fonctionnent
en mémoire pure (dictionnaires Python).

Fonctionnalités couvertes (IDs du catalogue) :
    6, 16, 32, 41, 42, 45, 47, 49, 50, 64, 67, 68, 70, 71, 72, 73,
    81, 82, 84, 88, 112, 113, 132, 134, 137, 143, 144
"""

from __future__ import annotations

import random
import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

TZ_KINSHASA = timezone(timedelta(hours=1))


# ================================================================
# STOCKAGE EN MÉMORE (fallback si DB indisponible)
# ================================================================

_MEM_DB: Dict[str, Any] = {}


def _mem(key: str, default=None):
    return _MEM_DB.get(key, default)


def _mem_set(key: str, value: Any):
    _MEM_DB[key] = value


# ================================================================
# Feature #6 - Mode Lingala et français
# ================================================================

TRADUCTIONS = {
    "fr": {
        "bonjour": "Bonjour",
        "prono_du_jour": "Pronostic du jour",
        "gagne": "Gagné",
        "perdu": "Perdu",
        "match_nul": "Match nul",
        "premium": "Premium",
        "gratuit": "Gratuit",
    },
    "lingala": {
        "bonjour": "Mbote",
        "prono_du_jour": "Prono ya lobi",
        "gagne": "Welesa",
        "perdu": "Kosinga",
        "match_nul": "Bilengi",
        "premium": "Premium",
        "gratuit": "Malamu",
    },
    "swahili": {
        "bonjour": "Hujambo",
        "prono_du_jour": "Proro ya leo",
        "gagne": "Umejisonga",
        "perdu": "Umeharibu",
        "match_nul": "Draw",
        "premium": "Premium",
        "gratuit": "Bure",
    },
}


def mode_lingala_francais(action: str = "get_langue", langue: str = "fr", cle: str = "bonjour") -> dict:
    """
    Gère le changement de langue et la traduction des messages.
    Aucune dépendance externe.
    """
    if action == "get_langue":
        return {
            "status": "complete",
            "feature_id": 6,
            "langue": langue,
            "message": TRADUCTIONS.get(langue, TRADUCTIONS["fr"]).get(cle, cle),
            "dependances": [],
        }
    if action == "set_langue":
        if langue not in TRADUCTIONS:
            return {"status": "erreur", "feature_id": 6, "message": "Langue non supportée", "dependances": []}
        _mem_set(f"langue_user_{action}", langue)
        return {
            "status": "complete",
            "feature_id": 6,
            "langue": langue,
            "message": "Langue mise à jour",
            "dependances": [],
        }
    # Traduction simple


# ================================================================
# Feature #16 - Avertissement jeu responsable
# ================================================================

def avertissement_jeu_responsable(historique_resultats: List[str], seuils_pertes_consecutives: int = 3) -> dict:
    """
    Détecte une série de pertes consécutives et propose une pause.
    """
    pertes_consecutives = 0
    for resultat in reversed(historique_resultats):
        if resultat == "perdu":
            pertes_consecutives += 1
        else:
            break

    doit_faire_pause = pertes_consecutives >= seuils_pertes_consecutives

    message = ""
    if doit_faire_pause:
        message = (
            f"⚠️ Vous avez enregistré {pertes_consecutives} perte(s) consécutive(s). "
            "Nous vous conseillons de faire une pause avant de continuer à parier."
        )
    else:
        message = "Aucune alerte jeu responsable nécessaire pour le moment."

    return {
        "status": "complete",


# ================================================================
# Feature #41 - Gestion Kelly automatique
# ================================================================

def gestion_kelly_automatique(bankroll: float, probabilite_estimee: float, cote_decimale: float, fraction_kelly: float = 0.25) -> dict:
    """
    Calcule la mise optimale selon le critère de Kelly fractionné.
    """
    if bankroll <= 0:
        return {"status": "erreur", "feature_id": 41, "message": "Bankroll invalide", "dependances": []}
    if not (0 < probabilite_estimee < 1):
        return {"status": "erreur", "feature_id": 41, "message": "Probabilité invalide", "dependances": []}
    if cote_decimale <= 1:
        return {"status": "erreur", "feature_id": 41, "message": "Cote invalide", "dependances": []}

    b = cote_decimale - 1
    p = probabilite_estimee
    q = 1 - p

    kelly_fraction = (p * b - q) / b
    kelly_fraction = max(0, kelly_fraction)

    mise_fractionne = kelly_fraction * fraction_kelly
    mise_mise = bankroll * mise_fractionne
    mise_mise = min(mise_mise, bankroll)

    gain_potentiel = mise_mise * cote_decimale
    benefice_potentiel = gain_potentiel - mise_mise

    return {
        "status": "complete",
        "feature_id": 41,
        "kelly_pur": round(kelly_fraction, 4),


# ================================================================
# Feature #42 - Plan de mise fixe ou progressif
# ================================================================

def plan_mise_fixe_progressif(
    bankroll: float,
    strategie: str = "fixe",
    mise_base: float = 0.02,
    numero_pari: int = 1,
    pertes_consecutives: int = 0,
) -> dict:
    """
    Calcule la mise selon la stratégie choisie :
    - 'fixe' : pourcentage constant de la bankroll
    - 'martingale_douce' : double après perte, reset après gain (capped)
    - 'fibonacci' : suit la suite de Fibonacci après perte
    """
    if bankroll <= 0:
        return {"status": "erreur", "feature_id": 42, "message": "Bankroll invalide", "dependances": []}

    if strategie == "fixe":
        mise = bankroll * mise_base
        message = f"Mise fixe : {mise_base*100}% de la bankroll"

    elif strategie == "martingale_douce":
        multiplicateur = 2 ** min(pertes_consecutives, 5)
        mise = bankroll * mise_base * multiplicateur
        mise = min(mise, bankroll)
        message = f"Martingale douce : x{multiplicateur} après {pertes_consecutives} perte(s)"

    elif strategie == "fibonacci":
        fib = [1, 1]
        for _ in range(max(pertes_consecutives, 0)):


# ================================================================
# Feature #45 - Assurance combiné
# ================================================================

def assurance_combine(
    mises: List[float],
    cotes: List[float],
    resultats: List[str],
    bonus_selections_echouees: int = 1,
) -> dict:
    """
    Calcule les gains d'un combiné avec assurance.
    """
    if len(mises) != len(cotes) or len(mises) != len(resultats):
        return {"status": "erreur", "feature_id": 45, "message": "Listes de tailles incohérentes", "dependances": []}

    mise_totale = sum(mises)
    gains_bruts = 0.0
    selections_gagnantes = 0
    selections_perdantes = 0

    for mise, cote, resultat in zip(mises, cotes, resultats):
        if resultat == "gagne":
            gains_bruts += mise * cote
            selections_gagnantes += 1
        elif resultat == "perdu":
            selections_perdantes += 1

    assurance_activee = 0 < selections_perdantes <= bonus_selections_echouees

    if assurance_activee:
        remboursement = mise_totale * 0.5
        net = remboursement - mise_totale


# ================================================================
# Feature #47 - Plan anti-perte
# ================================================================

def plan_anti_perte(
    historique_resultats: List[str],
    mise_souhaitee: float,
    pertes_consecutives_pour_blocage: int = 3,
    mise_max_apres_pertes: float = 0.0,
) -> dict:
    """
    Bloque ou réduit les gros combinés après une série de pertes.
    """
    pertes = 0
    for resultat in reversed(historique_resultats):
        if resultat == "perdu":
            pertes += 1
        else:
            break

    bloque = pertes >= pertes_consecutives_pour_blocage
    mise_autorisee = mise_souhaitee

    if bloque:
        mise_autorisee = 0.0
        message = (
            f"⛔ Plan anti-perte activé : {pertes} perte(s) consécutive(s). "
            "Les gros combinés sont bloqués jusqu'à nouveau gain."
        )
    elif mise_max_apres_pertes > 0 and pertes >= 1:
        mise_autorisee = min(mise_souhaitee, mise_max_apres_pertes)
        message = (
            f"⚠️ {pertes} perte(s) récente(s). Mise limitée à {mise_max_apres_pertes}."


# ================================================================
# Feature #50 - Notifications à l'heure de Kinshasa
# ================================================================

def notifications_heure_kinshasa(heure_heure: int = 9, minute: int = 0) -> dict:
    """
    Indique si c'est le moment d'envoyer les notifications (09h00 Kinshasa).
    Retourne aussi le délai avant la prochaine notification.
    """
    maintenant = datetime.now(TZ_KINSHASA)
    cible = maintenant.replace(hour=heure_heure, minute=minute, second=0, microsecond=0)

    if maintenant > cible:
        cible = cible + timedelta(days=1)

    delai = cible - maintenant
    heures = delai.seconds // 3600
    minutes = (delai.seconds % 3600) // 60

    est_maintenant = maintenant.hour == heure_heure and maintenant.minute == minute

    return {
        "status": "complete",
        "feature_id": 50,
        "heure_kinshasa": maintenant.strftime("%H:%M"),
        "heure_cible": f"{heure_heure:02d}:{minute:02d}",
        "est_maintenant": est_maintenant,
        "delai_heures": heures,
        "delai_minutes": minutes,
        "message": (
            "C'est l'heure des notifications Kinshasa !"
            if est_maintenant
            else f"Prochaine notification dans {heures}h{minutes:02d}min"


# ================================================================
# Feature #64 - Simulation Monte Carlo
# ================================================================

def simulation_monte_carlo(lambda_domicile: float, lambda_exterieur: float, simulations: int = 10000) -> dict:
    """
    Simule le déroulement d'un match `simulations` fois avec des lois de Poisson.
    Retourne les probabilités de 1, N, 2 et les scores les plus probables.
    """
    if simulations <= 0 or simulations > 200000:
        return {"status": "erreur", "feature_id": 64, "message": "Nombre de simulations invalide", "dependances": []}

    domicile_gagne = 0
    match_nul = 0
    exterieur_gagne = 0
    scores: Dict[str, int] = {}

    for _ in range(simulations):
        score_dom = random.poisson(lambda_domicile)
        score_ext = random.poisson(lambda_exterieur)

        if score_dom > score_ext:
            domicile_gagne += 1
        elif score_dom < score_ext:
            exterieur_gagne += 1
        else:
            match_nul += 1

        cle_score = f"{score_dom}-{score_ext}"
        scores[cle_score] = scores.get(cle_score, 0) + 1

    total = simulations
    scores_tries = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "status": "complete",
        "feature_id": 64,
        "simulations": total,


# ================================================================
# Feature #67 - Paris virtuels avec argent fictif
# ================================================================

class ParisVirtuels:
    """
    Gestion de bankroll fictive pour paris sans argent réel.
    """

    def __init__(self, solde_initial: float = 1000.0):
        self.solde_initial = solde_initial
        self.solde = solde_initial
        self.historique: List[dict] = []

    def placer_pari(self, mise: float, cote: float, resultat_gagne: bool) -> dict:
        if mise <= 0:
            return {"status": "erreur", "feature_id": 67, "message": "Mise invalide", "dependances": []}
        if mise > self.solde:
            return {"status": "erreur", "feature_id": 67, "message": "Solde insuffisant", "dependances": []}

        self.solde -= mise
        if resultat_gagne:
            gain = mise * cote
            self.solde += gain
            benefice = gain - mise
        else:
            benefice = -mise

        entree = {
            "mise": mise,
            "cote": cote,
            "gagne": resultat_gagne,
            "benefice": benefice,


# ================================================================
# Feature #71 - Bonus de connexion quotidienne
# ================================================================

def bonus_connexion_quotidienne(
    user_id: int,
    derniere_connexion: Optional[str] = None,
    xp_par_connexion: int = 10,
    bonus_streak: int = 5,
) -> dict:
    """
    Attribue des XP et récompenses cumulées à la connexion quotidienne.
    Gère le streak (jours consécutifs).
    """
    maintenant = datetime.now(TZ_KINSHASA).date()
    date_str = maintenant.isoformat()

    streak = 1
    if derniere_connexion:
        try:
            derniere = datetime.fromisoformat(derniere_connexion).date()
            if (maintenant - derniere).days == 1:
                streak = _mem(f"streak_{user_id}", 1) + 1
            elif (maintenant - derniere).days > 1:
                streak = 1
        except Exception:
            streak = 1

    _mem_set(f"streak_{user_id}", streak)
    _mem_set(f"derniere_connexion_{user_id}", date_str)

    xp_gagne = xp_par_connexion
    if streak >= 7:


# ================================================================
# Feature #81 - Notifications silencieuses
# ================================================================

def notifications_silencieuses(user_id: int, heure_report: int, activer: bool = True) -> dict:
    """
    Permet de reporter les alertes à une heure choisie (mode silencieux).
    """
    if not (0 <= heure_report <= 23):
        return {"status": "erreur", "feature_id": 81, "message": "Heure invalide", "dependances": []}

    _mem_set(f"silencieux_{user_id}", {"activer": activer, "heure": heure_report})

    return {
        "status": "complete",
        "feature_id": 81,
        "user_id": user_id,
        "activer": activer,
        "heure_report": heure_report,
        "message": (
            f"Notifications silencieuses activées. Report à {heure_report:02d}h."
            if activer else "Notifications silencieuses désactivées."
        ),
        "dependances": [],
    }


# ================================================================
# Feature #88 - Mode nuit économie de données
# ================================================================

def mode_nuit_economie_donnees(texte: str, activer: bool = True) -> dict:
    """
    Retourne une version ultra-légère du message (mode nuit).
    """
    if not activer:
        return {
            "status": "complete",


# ================================================================
# Feature #112 - Modération des mots interdits
# ================================================================

MOTS_INTERDITS_DEFAUT = ["insulte1", "insulte2", "spam", "lien_interdit"]

def moderation_mots_interdits(texte: str, mots_interdits: Optional[List[str]] = None) -> dict:
    """
    Détecte et supprime les mots interdits, liens et numéros dans un texte.
    """
    mots = mots_interdits or MOTS_INTERDITS_DEFAUT
    texte_net = texte
    trouves = []

    for mot in mots:
        if mot.lower() in texte_net.lower():
            trouves.append(mot)
            texte_net = re.sub(rf"\b{re.escape(mot)}\b", "[***]", texte_net, flags=re.IGNORECASE)

    # Détection de liens simples
    liens = re.findall(r"https?://\S+", texte_net)
    for lien in liens:
        texte_net = texte_net.replace(lien, "[LIEN]")

    return {
        "status": "complete",
        "feature_id": 112,
        "texte_original": texte,


# ================================================================
# Feature #132 - Logs d'erreurs lisibles
# ================================================================

def logs_erreurs_lisibles(erreur: Exception, contexte: Optional[dict] = None) -> dict:
    """
    Formate une erreur de manière compréhensible pour l'utilisateur/admin.
    """
    type_err = type(erreur).__name__
    message = str(erreur) if str(erreur) else "Erreur inconnue"

    # Simplification des messages techniques
    messages_simples = {
        "ConnectionError": "Connexion impossible. Vérifiez votre accès Internet.",
        "TimeoutError": "Délai d'attente dépassé. Réessayez plus tard.",
        "ValueError": "Valeur invalide fournie.",
        "KeyError": "Donnée manquante dans la requête.",
        "FileNotFoundError": "Fichier introuvable.",
        "PermissionError": "Accès refusé.",
    }

    message_lisible = messages_simples.get(type_err, message)

    return {
        "status": "complete",
        "feature_id": 132,
        "type_erreur": type_err,
        "message_lisible": message_lisible,
        "contexte": contexte or {},
        "horodatage": datetime.now(TZ_KINSHASA).isoformat(),
        "dependances": [],
    }


# ================================================================
# Feature #134 - Alerte pic d'erreurs
# ================================================================

def alerte_pic_erreurs(nb_erreurs: int, seuil: int = 5, fenetre_minutes: int = 5) -> dict:
    """
    Avertit si le nombre d'erreurs dépasse un seuil sur une fenêtre donnée.
    """
    depasse = nb_erreurs >= seuil

    return {
        "status": "complete",
        "feature_id": 134,
        "nb_erreurs": nb_erreurs,
        "seuil": seuil,
        "fenetre_minutes": fenetre_minutes,
        "depasse": depasse,
        "message": (
            f"🚨 Pic d'erreurs : {nb_erreurs} erreurs en {fenetre_minutes} min (seuil: {seuil})."
            if depasse
            else f"Nombre d'erreurs normal : {nb_erreurs} / {seuil}."
        ),
        "dependances": [],
    }


# ================================================================
# Feature #137 - Planificateur de tâches
# ================================================================

def planificateur_taches(tache: str, heure: str, active: bool = True) -> dict:
    """
    Planifie une tâche récurrente (entraînement modèle, nettoyage, etc.).
    """
    try:
        datetime.strptime(heure, "%H:%M")
    except ValueError:
        return {"status": "erreur", "feature_id": 137, "message": "Heure invalide (HH:MM)", "dependances": []}

    _mem_set(f"tache_planifiee_{tache}", {"heure": heure, "active": active})

    return {
        "status": "complete",
        "feature_id": 137,
        "tache": tache,
        "heure": heure,
        "active": active,
        "message": f"Tâche '{tache}' planifiée à {heure} (actif: {active}).",
        "dependances": [],
    }


# ================================================================
# Feature #143 - Commande /daily
# ================================================================

def cmd_daily(user_id: int, derniere_recompense: Optional[str] = None) -> dict:
    """
    Récupère le bonus de connexion quotidien (une fois par jour).
    """
    maintenant = datetime.now(TZ_KINSHASA).date()
    date_str = maintenant.isoformat()

    if derniere_recompense == date_str:
        return {
            "status": "erreur",
            "feature_id": 143,
            "message": "Bonus déjà récupéré aujourd'hui.",
            "dependances": [],
        }

    xp = 20
    pieces = 50
    _mem_set(f"daily_{user_id}", date_str)
    _mem_set(f"xp_{user_id}", _mem(f"xp_{user_id}", 0) + xp)
    _mem_set(f"pieces_{user_id}", _mem(f"pieces_{user_id}", 0) + pieces)

    return {
        "status": "complete",
        "feature_id": 143,
        "user_id": user_id,
        "date": date_str,
        "xp": xp,
        "pieces": pieces,
        "message": f"✅ Bonus quotidien : +{xp} XP et +{pieces} pièces !",
        "dependances": [],
    }


# ================================================================
# Feature #144 - Commande /roue
# ================================================================

def cmd_roue(user_id: int, derniere_roue: Optional[str] = None) -> dict:
    """
    Utilise la roue quotidienne gratuite (une fois par jour).
    """
    maintenant = datetime.now(TZ_KINSHASA).date()
    date_str = maintenant.isoformat()

    if derniere_roue == date_str:
        return {
            "status": "erreur",
            "feature_id": 144,
            "message": "Roue déjà utilisée aujourd'hui.",
            "dependances": [],
        }

    gains_possibles = [
        {"nom": "5 XP", "xp": 5, "prob": 50},
        {"nom": "15 XP", "xp": 15, "prob": 25},
        {"nom": "30 XP", "xp": 30, "prob": 15},
        {"nom": "50 XP", "xp": 50, "prob": 7},
        {"nom": "100 XP", "xp": 100, "prob": 3},
    ]
    poids = [g["prob"] for g in gains_possibles]
    gain = random.choices(gains_possibles, weights=poids, k=1)[0]

    _mem_set(f"roue_{user_id}", date_str)
    _mem_set(f"xp_{user_id}", _mem(f"xp_{user_id}", 0) + gain["xp"])

    return {
        "status": "complete",
        "feature_id": 144,
        "user_id": user_id,
        "date": date_str,
        "gain": gain["nom"],
        "xp_gagne": gain["xp"],
        "message": f"🎡 Roue : vous avez gagné {gain['nom']} !",
        "dependances": [],
    }

        "texte_nettoye": texte_net,
        "mots_trouves": trouves,
        "liens_trouves": liens,
        "est_propre": len(trouves) == 0 and len(liens) == 0,
        "dependances": [],
    }


# ================================================================
# Feature #113 - Anti-spam automatique
# ================================================================

def anti_spam_automatique(user_id: int, nb_messages_recent: int, seuil: int = 10) -> dict:
    """
    Mute temporaire si l'utilisateur envoie trop de messages.
    """
    deja_mute = _mem(f"mute_{user_id}", False)
    if deja_mute:
        return {
            "status": "complete",
            "feature_id": 113,
            "user_id": user_id,
            "mute": True,
            "message": "Utilisateur déjà en mute temporaire.",
            "dependances": [],
        }

    if nb_messages_recent >= seuil:
        _mem_set(f"mute_{user_id}", True)
        return {
            "status": "complete",
            "feature_id": 113,
            "user_id": user_id,
            "mute": True,
            "message": f"Mute temporaire : {nb_messages_recent} messages (seuil: {seuil}).",
            "dependances": [],
        }

    return {
        "status": "complete",
        "feature_id": 113,
        "user_id": user_id,
        "mute": False,
        "message": "Aucun spam détecté.",
        "dependances": [],
    }

            "feature_id": 88,
            "texte": texte,
            "taille_octets": len(texte.encode("utf-8")),
            "dependances": [],
        }

    # Version allégée : supprime émojis, espaces multiples, retours ligne superflus
    import re

    texte_allonge = texte
    texte_allonge = re.sub(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u27BF]", "", texte_allonge)
    texte_allonge = re.sub(r"\n{2,}", "\n", texte_allonge)
    texte_allonge = re.sub(r" {2,}", " ", texte_allonge)
    texte_allonge = texte_allonge.strip()

    return {
        "status": "complete",
        "feature_id": 88,
        "texte_original": texte,
        "texte_allonge": texte_allonge,
        "taille_originale_octets": len(texte.encode("utf-8")),
        "taille_allongee_octets": len(texte_allonge.encode("utf-8")),
        "economie_pourcent": round(
            (1 - len(texte_allonge.encode("utf-8")) / max(len(texte.encode("utf-8"), 1))) * 100, 2
        ),
        "dependances": [],
    }

        xp_gagne += bonus_streak * 2
    elif streak >= 3:
        xp_gagne += bonus_streak

    total_xp = _mem(f"xp_total_{user_id}", 0) + xp_gagne
    _mem_set(f"xp_total_{user_id}", total_xp)

    return {
        "status": "complete",
        "feature_id": 71,
        "user_id": user_id,
        "date": date_str,
        "streak": streak,
        "xp_gagne": xp_gagne,
        "xp_total": total_xp,
        "message": f"Connexion quotidienne ! +{xp_gagne} XP (streak: {streak} jour(s)).",
        "dependances": [],
    }


# ================================================================
# Feature #72 - Roue quotidienne gratuite
# ================================================================

def roue_quotidienne(user_id: int, derniere_utilisation: Optional[str] = None) -> dict:
    """
    Tirage aléatoire : prix aléatoires, XP ou remise.
    Une seule fois par jour par utilisateur.
    """
    maintenant = datetime.now(TZ_KINSHASA).date()
    date_str = maintenant.isoformat()

    if derniere_utilisation == date_str:
        return {
            "status": "erreur",
            "feature_id": 72,
            "message": "Roue déjà utilisée aujourd'hui",
            "dependances": [],
        }

    prix = [
        {"nom": "10 XP", "type": "xp", "valeur": 10, "probabilite": 40},
        {"nom": "25 XP", "type": "xp", "valeur": 25, "probabilite": 25},
        {"nom": "50 XP", "type": "xp", "valeur": 50, "probabilite": 15},
        {"nom": "Remise 10%", "type": "remise", "valeur": 10, "probabilite": 10},
        {"nom": "Remise 25%", "type": "remise", "valeur": 25, "probabilite": 7},
        {"nom": "Premium 1 jour", "type": "premium", "valeur": 1, "probabilite": 3},
    ]

    # Tirage pondéré
    poids = [p["probabilite"] for p in prix]
    choix = random.choices(prix, weights=poids, k=1)[0]

    _mem_set(f"roue_derniere_{user_id}", date_str)

    return {
        "status": "complete",
        "feature_id": 72,
        "user_id": user_id,
        "date": date_str,
        "prix": choix["nom"],
        "type": choix["type"],
        "valeur": choix["valeur"],
        "message": f"🎡 Vous avez gagné : {choix['nom']} !",
        "dependances": [],
    }


# ================================================================
# Feature #73 - Classement des parrains
# ================================================================

def classement_parrains(parrains: List[dict]) -> dict:
    """
    Trône les meilleurs parrains selon le nombre de filleuls et points.
    """
    if not parrains:
        return {"status": "complete", "feature_id": 73, "classement": [], "message": "Aucun parrain", "dependances": []}

    tries = sorted(
        parrains,
        key=lambda p: (p.get("filleuls", 0), p.get("points", 0)),
        reverse=True,
    )

    classement = []
    for rang, p in enumerate(tries, 1):
        classement.append({
            "rang": rang,
            "user_id": p.get("user_id"),
            "nom": p.get("nom", "Inconnu"),
            "filleuls": p.get("filleuls", 0),
            "points": p.get("points", 0),
        })

    return {
        "status": "complete",
        "feature_id": 73,
        "classement": classement,
        "message": "Classement des parrains mis à jour.",
        "dependances": [],
    }

            "solde_apres": self.solde,
        }
        self.historique.append(entree)
        return {"status": "complete", "feature_id": 67, "entree": entree, "dependances": []}

    def etat(self) -> dict:
        return {
            "status": "complete",
            "feature_id": 67,
            "solde_initial": self.solde_initial,
            "solde_actuel": round(self.solde, 2),
            "benefice_total": round(self.solde - self.solde_initial, 2),
            "nb_paris": len(self.historique),
            "dependances": [],
        }


# ================================================================
# Feature #68 - Ligue privée entre amis
# ================================================================

class LiguePrivee:
    """
    Groupe de compétition privé entre amis.
    """

    def __init__(self, nom: str, createur_id: int):
        self.nom = nom
        self.createur_id = createur_id
        self.membres: Dict[int, dict] = {createur_id: {"points": 0, "paris": 0}}
        self.classement: List[dict] = []

    def ajouter_membre(self, user_id: int) -> dict:
        if user_id in self.membres:
            return {"status": "erreur", "feature_id": 68, "message": "Déjà membre", "dependances": []}
        self.membres[user_id] = {"points": 0, "paris": 0}
        return {"status": "complete", "feature_id": 68, "message": "Membre ajouté", "dependances": []}

    def enregistrer_pari(self, user_id: int, points: int) -> dict:
        if user_id not in self.membres:
            return {"status": "erreur", "feature_id": 68, "message": "Utilisateur non membre", "dependances": []}
        self.membres[user_id]["points"] += points
        self.membres[user_id]["paris"] += 1
        self._recalculer_classement()
        return {"status": "complete", "feature_id": 68, "message": "Points ajoutés", "dependances": []}

    def _recalculer_classement(self):
        self.classement = sorted(
            [{"user_id": uid, **info} for uid, info in self.membres.items()],
            key=lambda x: x["points"],
            reverse=True,
        )

    def etat(self) -> dict:
        return {
            "status": "complete",
            "feature_id": 68,
            "nom": self.nom,
            "createur_id": self.createur_id,
            "nb_membres": len(self.membres),
            "classement": self.classement,
            "dependances": [],
        }


# ================================================================
# Feature #70 - Boutique XP
# ================================================================

def boutique_xp(points_disponibles: int, cout_recompense: int, type_recompense: str = "premium") -> dict:
    """
    Échange des points XP contre une récompense (Premium, analyse VIP, etc.).
    """
    if points_disponibles < cout_recompense:
        return {
            "status": "erreur",
            "feature_id": 70,
            "message": "Points insuffisants",
            "points_manquants": cout_recompense - points_disponibles,
            "dependances": [],
        }

    points_restants = points_disponibles - cout_recompense
    return {
        "status": "complete",
        "feature_id": 70,
        "recompense": type_recompense,
        "cout": cout_recompense,
        "points_restants": points_restants,
        "message": f"Récompense '{type_recompense}' achetée pour {cout_recompense} XP.",
        "dependances": [],
    }

        "p_domicile": round(domicile_gagne / total, 4),
        "p_nul": round(match_nul / total, 4),
        "p_exterieur": round(exterieur_gagne / total, 4),
        "cote_juste_domicile": round(total / domicile_gagne, 2) if domicile_gagne > 0 else None,
        "cote_juste_nul": round(total / match_nul, 4) if match_nul > 0 else None,
        "cote_juste_exterieur": round(total / exterieur_gagne, 2) if exterieur_gagne > 0 else None,
        "scores_plus_probables": scores_tries,
        "dependances": [],
    }

        ),
        "dependances": [],
    }

        )
    else:
        message = "Mise autorisée. Aucun blocage anti-perte."

    return {
        "status": "complete",
        "feature_id": 47,
        "pertes_consecutives": pertes,
        "bloque": bloque,
        "mise_autorisee": round(mise_autorisee, 2),
        "mise_souhaitee": round(mise_souhaitee, 2),
        "message": message,
        "dependances": [],
    }


# ================================================================
# Feature #49 - Dashboard ROI personnel
# ================================================================

def dashboard_roi_personnel(mises: List[float], gains: List[float]) -> dict:
    """
    Calcule le rendement (ROI) d'un utilisateur sur une période.
    """
    if not mises or not gains or len(mises) != len(gains):
        return {"status": "erreur", "feature_id": 49, "message": "Données incohérentes", "dependances": []}

    mise_totale = sum(mises)
    gain_total = sum(gains)
    benefice_net = gain_total - mise_totale
    roi = (benefice_net / mise_totale * 100) if mise_totale > 0 else 0.0
    nb_paris = len(mises)
    nb_gagnes = sum(1 for g in gains if g > 0)
    taux_reussite = (nb_gagnes / nb_paris * 100) if nb_paris > 0 else 0.0

    return {
        "status": "complete",
        "feature_id": 49,
        "mise_totale": round(mise_totale, 2),
        "gain_total": round(gain_total, 2),
        "benefice_net": round(benefice_net, 2),
        "roi_pourcent": round(roi, 2),
        "nb_paris": nb_paris,
        "nb_gagnes": nb_gagnes,
        "taux_reussite_pourcent": round(taux_reussite, 2),
        "dependances": [],
    }

        message = (
            f"Assurance activée : {selections_perdantes} sélection(s) échouée(s). "
            f"Remboursement de {round(remboursement, 2)} (50% de la mise)."
        )
    else:
        remboursement = 0.0
        net = gains_bruts - mise_totale
        if selections_perdantes == 0:
            message = "Combiné gagné : toutes les sélections sont validées."
        else:
            message = "Combiné perdu : trop de sélections échouées pour l'assurance."

    return {
        "status": "complete",
        "feature_id": 45,
        "mise_totale": round(mise_totale, 2),
        "gains_bruts": round(gains_bruts, 2),
        "selections_gagnantes": selections_gagnantes,
        "selections_perdantes": selections_perdantes,
        "assurance_activee": assurance_activee,
        "remboursement": round(remboursement, 2),
        "net": round(net, 2),
        "message": message,
        "dependances": [],
    }

            fib.append(fib[-1] + fib[-2])
        coef = fib[min(pertes_consecutives, len(fib) - 1)]
        mise = bankroll * mise_base * coef
        mise = min(mise, bankroll)
        message = f"Fibonacci : coeff {coef} après {pertes_consecutives} perte(s)"

    else:
        return {"status": "erreur", "feature_id": 42, "message": "Stratégie inconnue", "dependances": []}

    mise = round(mise, 2)
    return {
        "status": "complete",
        "feature_id": 42,
        "strategie": strategie,
        "mise": mise,
        "pourcentage_bankroll": round(mise / bankroll * 100, 2),
        "message": message,
        "dependances": [],
    }

        "fraction_appliquee": fraction_kelly,
        "mise_recommandee": round(mise_mise, 2),
        "pourcentage_bankroll": round(mise_fractionne * 100, 2),
        "gain_potentiel": round(gain_potentiel, 2),
        "benefice_potentiel": round(benefice_potentiel, 2),
        "dependances": [],
    }

        "feature_id": 16,
        "pertes_consecutives": pertes_consecutives,
        "doit_faire_pause": doit_faire_pause,
        "message": message,
        "dependances": [],
    }

    texte = TRADUCTIONS.get(langue, TRADUCTIONS["fr"]).get(cle, cle)
    return {
        "status": "complete",
        "feature_id": 6,
        "langue": langue,
        "texte_traduit": texte,
        "dependances": [],
    }


def mode_swahili(action: str = "get", cle: str = "bonjour") -> dict:
    """
    Traduction adaptée à l'Est de la RDC (Swahili).
    Aucune dépendance externe.
    """
    texte = TRADUCTIONS["swahili"].get(cle, cle)
    return {
        "status": "complete",
        "feature_id": 82,
        "texte_traduit": texte,
        "dependances": [],
    }
