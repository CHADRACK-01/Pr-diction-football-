"""
Gestion du mode panique persistant.

Le flag 'mode_panique' est stocké dans la table parametres via
set_parametre() / get_parametre() de users.admin.
"""

from users.admin import set_parametre, get_parametre


CLE_MODE_PANIQUE = 'mode_panique'


def activer_panique():
    """Active le mode panique (écrit 'true' dans le paramètre 'mode_panique')."""
    return set_parametre(CLE_MODE_PANIQUE, 'true', "Mode panique actif")


def desactiver_panique():
    """Désactive le mode panique (écrit 'false' dans le paramètre 'mode_panique')."""
    return set_parametre(CLE_MODE_PANIQUE, 'false', "Mode panique inactif")


def est_en_panique() -> bool:
    """Indique si le mode panique est actif (False par défaut en cas d'erreur de lecture)."""
    return str(get_parametre(CLE_MODE_PANIQUE, 'false')).strip().lower() == 'true'
