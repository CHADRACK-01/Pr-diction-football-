# app.py - Point d'entrée WSGI / CLI
"""
Point d'entrée de l'application Prédiction Football.

Ajoute src/ au path Python et délègue vers src.app.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.app import *  # noqa: F401, F403
