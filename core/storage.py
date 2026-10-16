import os
import requests
from config import (
    UPSTASH_BLOB_TOKEN, UPSTASH_BUCKET_NAME,
    DOSSIER_PASSE, DOSSIER_ACTUEL
)

# API REST Upstash Blob
BASE_URL = f"https://{UPSTASH_BUCKET_NAME}.blob.upstash.io"


def _headers():
    return {
        "Authorization": f"Bearer {UPSTASH_BLOB_TOKEN}",
        "Content-Type": "application/octet-stream",
    }


def upload_file(chemin_local, cle_upstash):
    """Envoie un fichier vers Upstash Blob."""
    if not UPSTASH_BLOB_TOKEN:
        print("⚠️ Token Upstash non configuré, upload ignoré.")
        return False

    try:
        with open(chemin_local, "rb") as f:
            data = f.read()

        url = f"{BASE_URL}/{cle_upstash}"
        response = requests.put(url, headers=_headers(), data=data, timeout=30)

        if response.status_code in (200, 201):
            return True
        else:
            print(f"❌ Upload {cle_upstash} : HTTP {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erreur upload {cle_upstash} : {e}")
        return False


def download_file(cle_upstash, chemin_local):
    """Télécharge un fichier depuis Upstash Blob."""
    if not UPSTASH_BLOB_TOKEN:
        return False

    try:
        url = f"{BASE_URL}/{cle_upstash}"
        response = requests.get(url, headers=_headers(), timeout=30)

        if response.status_code == 200:
            os.makedirs(os.path.dirname(chemin_local), exist_ok=True)
            with open(chemin_local, "wb") as f:
                f.write(response.content)
            return True
        elif response.status_code == 404:
            return False
        else:
            print(f"⚠️ Download {cle_upstash} : HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur download {cle_upstash} : {e}")
        return False


def list_files(prefixe=""):
    """Liste les fichiers dans Upstash Blob avec un préfixe."""
    if not UPSTASH_BLOB_TOKEN:
        return []

    try:
        url = f"{BASE_URL}/list"
        params = {"prefix": prefixe} if prefixe else {}
        response = requests.get(url, headers=_headers(), params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("result", [])
        return []
    except Exception as e:
        print(f"❌ Erreur list {prefixe} : {e}")
        return []


def upload_folder_to_upstash(dossier_local, prefixe):
    """Envoie tous les fichiers d'un dossier local vers Upstash Blob."""
    if not os.path.exists(dossier_local):
        print(f"⚠️ Dossier {dossier_local} introuvable, upload ignoré.")
        return

    print(f"☁️ Envoi de {dossier_local} vers Upstash...")
    for racine, _, fichiers in os.walk(dossier_local):
        for fichier in fichiers:
            chemin_local = os.path.join(racine, fichier)
            cle = f"{prefixe}/{fichier}"
            upload_file(chemin_local, cle)
    print("☁️ Upload Upstash terminé.")


def download_folder_from_upstash(prefixe, dossier_local):
    """Télécharge les fichiers de Upstash Blob vers un dossier local."""
    if not UPSTASH_BLOB_TOKEN:
        return

    os.makedirs(dossier_local, exist_ok=True)
    print(f"☁️ Récupération de {prefixe} depuis Upstash...")

    fichiers = list_files(prefixe)
    if not fichiers:
        print(f"ℹ️ Aucun fichier trouvé sur Upstash pour le préfixe '{prefixe}'.")
        return

    for cle in fichiers:
        nom_fichier = os.path.basename(cle)
        if not nom_fichier:
            continue
        chemin_local = os.path.join(dossier_local, nom_fichier)
        download_file(cle, chemin_local)

    print(f"☁️ Récupération Upstash terminée ({len(fichiers)} fichier(s)).")
