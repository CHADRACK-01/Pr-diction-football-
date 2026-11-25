# config.py - Configuration centrale
"""
Configuration du bot Prédiction Football.

Réexporte tout depuis src/config.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.config import *  # noqa: F401, F403
