# Package users - Gestion complète des utilisateurs et données

from users.db import (
    get_connection,
    initialiser_tables
)

from users.matchs import (
    inserer_matchs,
    charger_tous_les_matchs,
    compter_matchs
)

from users.model_cache import (
    sauvegarder_modele_cache,
    charger_modele_cache,
    vider_modele_cache
)

from users.accounts import (
    utilisateur_existe,
    get_user_info,
    get_user_status,
    enregistrer_utilisateur,
    set_premium,
    est_premium,
    get_statut_label,
    incrementer_compteur,
    get_compteur_jour,
    get_limite_jour,
    peut_faire_pronostic,
    activer_notifications,
    desactiver_notifications,
    get_utilisateurs_notifies,
    get_tous_utilisateurs,
    get_langue,
    set_langue,
    get_parrain,
    set_parrain,
    compter_filleuls,
    ajouter_jours_premium
)
from users.admin import (
    get_parametre,
    set_parametre,
    get_tous_parametres,
    est_administrateur,
    ajouter_admin,
    retirer_admin,
    get_tous_admins,
    est_banni,
    bannir_user,
    debannir_user,
    get_liste_bannis,
    log_admin,
    get_logs_admin,
    get_stats_globales,
    get_liste_utilisateurs
)
