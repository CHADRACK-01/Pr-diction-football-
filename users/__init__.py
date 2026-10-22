# Package users - Gestion des utilisateurs, base de données et paiements

# =========================================================
# BASE DE DONNÉES
# =========================================================
from users.db import (
    get_connection,
    initialiser_tables,
    get_taille_base,
    get_detail_tables,
    nettoyer_logs_anciens,
    nettoyer_paiements_anciens
)

# =========================================================
# COMPTES UTILISATEURS (BASE)
# =========================================================
from users.account_base import (
    utilisateur_existe,
    get_user_info,
    get_user_status,
    enregistrer_utilisateur,
    set_premium,
    est_premium,
    get_statut_label,
    get_langue,
    set_langue
)

# =========================================================
# LIMITES ET COMPTEURS
# =========================================================
from users.account_limits import (
    incrementer_compteur,
    get_compteur_jour,
    get_limite_jour,
    peut_faire_pronostic,
    ajouter_jours_premium
)

# =========================================================
# NOTIFICATIONS
# =========================================================
from users.account_notifications import (
    activer_notifications,
    desactiver_notifications,
    get_utilisateurs_notifies,
    get_tous_utilisateurs
)

# =========================================================
# PARRAINAGE
# =========================================================
from users.account_referral import (
    get_parrain,
    set_parrain,
    compter_filleuls,
    get_top_parrains,
    get_filleuls,
    get_palier_atteint,
    get_prochain_palier
)

# =========================================================
# MATCHS
# =========================================================
from users.matchs import (
    inserer_matchs,
    charger_tous_les_matchs,
    compter_matchs
)

# =========================================================
# CACHE DU MODÈLE
# =========================================================
from users.model_cache import (
    sauvegarder_modele_cache,
    charger_modele_cache,
    vider_modele_cache
)

# =========================================================
# PAIEMENTS ET CODES
# =========================================================
from users.paiements import (
    creer_demande_paiement,
    get_demande,
    get_demandes_en_attente,
    valider_demande,
    refuser_demande,
    compter_demandes_en_attente,
    generer_code,
    generer_lot_codes,
    utiliser_code,
    get_codes_disponibles,
    get_codes_utilises,
    compter_codes_disponibles
)

# =========================================================
# ADMINISTRATION
# =========================================================
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
