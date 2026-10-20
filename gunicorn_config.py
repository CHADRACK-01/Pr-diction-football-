import os

# Render fournit le port via la variable d'environnement PORT
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# ⚠️ CRUCIAL : On garde 1 seul worker pour ne pas dupliquer la RAM (512 Mo max)
workers = 1

# ⚠️ CRUCIAL : On utilise 'gthread' pour gérer plusieurs requêtes en parallèle
# sans bloquer le CPU sur une seule tâche lourde
worker_class = "gthread"
threads = 4

# On augmente le timeout pour laisser le temps aux calculs de Poisson
timeout = 120

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
