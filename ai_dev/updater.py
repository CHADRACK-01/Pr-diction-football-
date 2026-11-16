# ai_dev/updater.py
"""
Gestionnaire de mise à jour.
Applique le code généré par l'IA avec backup et push GitHub automatique.
Gère la création de nouveaux fichiers (pas de backup nécessaire).
"""

import os
import shutil
import subprocess
from datetime import datetime
from core.utils.logs import log_info, log_error, log_warning

BACKUP_DIR = "backups_ia"

def _creer_backup(chemin_fichier):
    """Crée une copie de sauvegarde du fichier original (si le fichier existe)."""
    # Si le fichier n'existe pas, pas besoin de backup (c'est une création)
    if not os.path.exists(chemin_fichier):
        log_info(f"Pas de backup nécessaire : {chemin_fichier} est un nouveau fichier.", "AI_UPDATER")
        return "NO_BACKUP_NEEDED"

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        nom_fichier = os.path.basename(chemin_fichier)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chemin_backup = os.path.join(BACKUP_DIR, f"{nom_fichier}.{timestamp}.bak")
        
        shutil.copy2(chemin_fichier, chemin_backup)
        log_info(f"Backup créé : {chemin_backup}", "AI_UPDATER")
        return chemin_backup
    except Exception as e:
        log_error(f"Impossible de créer le backup de {chemin_fichier}", "AI_UPDATER", exception=e)
        return None

def _git_commit_and_push(chemin_fichier, message):
    """Envoie la modification sur GitHub pour déclencher le redéploiement Render."""
    try:
        # On se place à la racine du projet (là où se trouve .git)
        projet_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Configuration Git locale
        subprocess.run(["git", "config", "user.email", "bot@pronostic.com"], cwd=projet_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Bot Auto-Update"], cwd=projet_dir, check=True)
        
        # Ajout du fichier modifié (ou créé)
        subprocess.run(["git", "add", chemin_fichier], cwd=projet_dir, check=True)
        
        # Commit
        subprocess.run(["git", "commit", "-m", f"🤖 IA Update: {message}"], cwd=projet_dir, check=True)
        
        # Push avec le token GitHub
        token = os.environ.get("GITHUB_TOKEN")
        repo_url = os.environ.get("GITHUB_REPO_URL")
        
        if not token or not repo_url:
            return False, "❌ GITHUB_TOKEN ou GITHUB_REPO_URL manquant dans les variables d'environnement."
            
        # Remplacement de l'URL pour l'authentification
        auth_url = repo_url.replace("https://", f"https://{token}@")
        subprocess.run(["git", "push", auth_url, "HEAD:main"], cwd=projet_dir, check=True)
        
        return True, "✅ Code poussé sur GitHub. Render va redéployer."
    except subprocess.CalledProcessError as e:
        log_error(f"Erreur Git: {e}", "AI_UPDATER", exception=e)
        return False, f"❌ Erreur lors du push GitHub : {str(e)}"
    except Exception as e:
        log_error(f"Erreur inattendue Git: {e}", "AI_UPDATER", exception=e)
        return False, f"❌ Erreur inattendue : {str(e)}"

def appliquer_mise_a_jour(chemin_fichier_original, chemin_fichier_test):
    """
    Applique le code testé sur le vrai fichier (avec backup + push git).
    Retourne (succes: bool, message: str).
    """
    log_info(f"Tentative d'application de la MAJ sur {chemin_fichier_original}", "AI_UPDATER")

    if not os.path.exists(chemin_fichier_test):
        return False, "❌ Fichier de test introuvable. Mise à jour annulée."

    # Création du backup (ou détection que c'est un nouveau fichier)
    backup = _creer_backup(chemin_fichier_original)
    if backup is None:
        return False, "❌ Impossible de créer le backup. Mise à jour annulée par sécurité."

    try:
        # 1. On écrase le fichier original avec le code testé (ou on le crée)
        shutil.copy2(chemin_fichier_test, chemin_fichier_original)
        
        # 2. On nettoie le fichier de test
        os.remove(chemin_fichier_test)
        
        # 3. On push vers GitHub
        succes_git, msg_git = _git_commit_and_push(chemin_fichier_original, "Mise à jour automatique par l'IA")
        
        if not succes_git:
            # Si le push échoue, on restaure le backup (si on en a un)
            if backup != "NO_BACKUP_NEEDED":
                shutil.copy2(backup, chemin_fichier_original)
            return False, f"❌ Échec du push GitHub. Rollback effectué.\n{msg_git}"
            
        return True, f"✅ Mise à jour appliquée et envoyée sur GitHub.\n{msg_git}"
        
    except Exception as e:
        log_error(f"Erreur critique lors de l'application de la MAJ", "AI_UPDATER", exception=e)
        try:
            if backup != "NO_BACKUP_NEEDED":
                shutil.copy2(backup, chemin_fichier_original)
            return False, f"❌ Erreur : {str(e)}. Le fichier original a été restauré."
        except Exception as e2:
            log_error(f"ÉCHEC CRITIQUE DU ROLLBACK", "AI_UPDATER", exception=e2)
            return False, f"❌❌ ERREUR CRITIQUE ! Impossible de restaurer.\nBackup manuel : `{backup}`"

def restaurer_backup(chemin_backup, chemin_fichier_original):
    """Restaure une sauvegarde spécifique."""
    try:
        if not os.path.exists(chemin_backup):
            return False, "❌ Fichier de backup introuvable."
        shutil.copy2(chemin_backup, chemin_fichier_original)
        log_info(f"Restauration effectuée depuis {chemin_backup}", "AI_UPDATER")
        return True, "✅ Fichier restauré avec succès."
    except Exception as e:
        log_error(f"Erreur de restauration", "AI_UPDATER", exception=e)
        return False, f"❌ Erreur de restauration : {str(e)}"
