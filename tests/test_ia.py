from core.feature_flags import est_active

if est_active("999"):
    def salutation():
        return "Bonjour, l'IA fonctionne !"
