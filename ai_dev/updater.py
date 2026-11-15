# ai_dev/updater.py
"""
Gestionnaire de mise à jour.
Applique le code généré par l'IA avec un système de sauvegarde (backup).
"""

import os
import shutil
from datetime import datetime
from core.utils.logs import log_info, log_error

BACKUP_DIR = "backups_ia"

def _creer_backup(chemin_fichier):
    """Crée une copie de sauvegarde du fichier original."""
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

def appliquer_mise_a_jour(chemin_fichier_original, chemin_fichier_test):
    """
    Applique le code testé sur le vrai fichier (avec backup).
    Retourne (succes: bool, message: str).
    """
    log_info(f"Tentative d'application de la MAJ sur {chemin_fichier_original}", "AI_UPDATER")

    # 1. Sécurité : on vérifie que le fichier de test existe
    if not os.path.exists(chemin_fichier_test):
        return False, "❌ Fichier de test introuvable. Mise à jour annulée."

    # 2. Backup du fichier original
    backup = _creer_backup(chemin_fichier_original)
    if not backup:
        return False, "❌ Impossible de créer le backup. Mise à jour annulée par sécurité."

    # 3. Application de la modification
    try:
        shutil.copy2(chemin_fichier_test, chemin_fichier_original)
        
        # 4. Nettoyage du fichier de test
        os.remove(chemin_fichier_test)
        
        log_info(f"MAJ appliquée avec succès sur {chemin_fichier_original}", "AI_UPDATER")
        return True, f"✅ Mise à jour appliquée avec succès.\n\n💾 Sauvegarde disponible : `{backup}`"
        
    except Exception as e:
        log_error(f"Erreur critique lors de l'application de la MAJ", "AI_UPDATER", exception=e)
        # 5. En cas d'erreur, on tente de restaurer automatiquement le backup
        try:
            shutil.copy2(backup, chemin_fichier_original)
            return False, "❌ Erreur lors de l'application. Le fichier original a été restauré automatiquement."
        except Exception as e2:
            log_error(f"ÉCHEC CRITIQUE DU ROLLBACK", "AI_UPDATER", exception=e2)
            return False, f"❌❌ ERREUR CRITIQUE ! Impossible de restaurer le fichier.\nBackup manuel : `{backup}`"

def restaurer_backup(chemin_backup, chemin_fichier_original):
    """Restaure une sauvegarde spécifique (bouton 'Revenir en arrière')."""
    try:
        if not os.path.exists(chemin_backup):
            return False, "❌ Fichier de backup introuvable."
            
        shutil.copy2(chemin_backup, chemin_fichier_original)
        log_info(f"Restauration effectuée depuis {chemin_backup}", "AI_UPDATER")
        return True, "✅ Fichier restauré avec succès."
    except Exception as e:
        log_error(f"Erreur de restauration", "AI_UPDATER", exception=e)
        return False, f"❌ Erreur de restauration : {str(e)}"
