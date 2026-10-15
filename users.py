import csv
import os
from datetime import datetime

from config import (
    FICHIER_UTILISATEURS, FICHIER_COMPTEURS,
    LIMITE_FREE_JOUR, LIMITE_PREMIUM_JOUR
)

# =========================================================
# INITIALISATION
# =========================================================
def initialiser_fichier_utilisateurs():
    """Crée le CSV des utilisateurs s'il n'existe pas."""
    if not os.path.exists(FICHIER_UTILISATEURS):
        with open(FICHIER_UTILISATEURS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'user_id', 'username', 'first_name',
                'status', 'date_inscription', 'date_expiration'
            ])
        print(f"📄 Fichier {FICHIER_UTILISATEURS} créé.")

def _initialiser_compteurs():
    """Crée le CSV des compteurs s'il n'existe pas."""
    if not os.path.exists(FICHIER_COMPTEURS):
        with open(FICHIER_COMPTEURS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'date', 'compteur'])


# =========================================================
# LECTURE
# =========================================================
def utilisateur_existe(user_id):
    if not os.path.exists(FICHIER_UTILISATEURS):
        return False
    with open(FICHIER_UTILISATEURS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['user_id'] and int(row['user_id']) == user_id:
                return True
    return False

def get_user_info(user_id):
    """Retourne le dict complet de l'utilisateur, ou None."""
    if not os.path.exists(FICHIER_UTILISATEURS):
        return None
    with open(FICHIER_UTILISATEURS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['user_id'] and int(row['user_id']) == user_id:
                return row
    return None

def get_user_status(user_id):
    """Retourne (status, date_expiration)."""
    info = get_user_info(user_id)
    if not info:
        return 'free', ''
    return info['status'], info['date_expiration']


# =========================================================
# ÉCRITURE
# =========================================================
def enregistrer_utilisateur(user_id, username, first_name):
    """Enregistre un nouvel utilisateur avec statut 'free'."""
    initialiser_fichier_utilisateurs()
    if utilisateur_existe(user_id):
        return False
    with open(FICHIER_UTILISATEURS, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            user_id,
            username or "",
            first_name or "",
            'free',
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            ""
        ])
    print(f"👤 Nouvel utilisateur : {first_name} ({user_id})")
    return True


def set_premium(user_id, date_expiration):
    """
    Passe un utilisateur en premium avec une date d'expiration.
    Format date_expiration : 'YYYY-MM-DD HH:MM'
    Retourne True si succès, False sinon.
    """
    if not os.path.exists(FICHIER_UTILISATEURS):
        print(f"⚠️ Fichier utilisateurs introuvable.")
        return False

    lignes = []
    trouve = False

    with open(FICHIER_UTILISATEURS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['user_id'] and int(row['user_id']) == user_id:
                row['status'] = 'premium'
                row['date_expiration'] = date_expiration
                trouve = True
            lignes.append(row)

    if not trouve:
        print(f"⚠️ Utilisateur {user_id} introuvable dans le CSV.")
        return False

    with open(FICHIER_UTILISATEURS, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(lignes)

    print(f"⭐ Utilisateur {user_id} passé en PREMIUM jusqu'au {date_expiration}")
    return True


# =========================================================
# STATUT
# =========================================================
def est_premium(user_id):
    """Vérifie si premium ET non expiré."""
    status, expiration = get_user_status(user_id)
    if status != 'premium':
        return False
    if not expiration:
        return False
    try:
        date_exp = datetime.strptime(expiration, "%Y-%m-%d %H:%M")
        return date_exp > datetime.now()
    except Exception:
        return False

def get_statut_label(user_id):
    return "⭐ PREMIUM" if est_premium(user_id) else "🆓 FREE"


# =========================================================
# LIMITES JOURNALIÈRES
# =========================================================
def incrementer_compteur(user_id):
    """Incrémente le compteur du jour pour cet utilisateur."""
    _initialiser_compteurs()
    today = datetime.now().strftime("%Y-%m-%d")
    lignes = []
    trouve = False

    with open(FICHIER_COMPTEURS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['user_id']) == user_id and row['date'] == today:
                row['compteur'] = int(row['compteur']) + 1
                trouve = True
            lignes.append(row)

    if not trouve:
        lignes.append({'user_id': user_id, 'date': today, 'compteur': 1})

    with open(FICHIER_COMPTEURS, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['user_id', 'date', 'compteur'])
        writer.writeheader()
        writer.writerows(lignes)

def get_compteur_jour(user_id):
    """Retourne le nombre de pronostics faits aujourd'hui."""
    _initialiser_compteurs()
    today = datetime.now().strftime("%Y-%m-%d")
    with open(FICHIER_COMPTEURS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['user_id']) == user_id and row['date'] == today:
                return int(row['compteur'])
    return 0

def get_limite_jour(user_id):
    return LIMITE_PREMIUM_JOUR if est_premium(user_id) else LIMITE_FREE_JOUR

def peut_faire_pronostic(user_id):
    return get_compteur_jour(user_id) < get_limite_jour(user_id)
