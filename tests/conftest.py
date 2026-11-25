# tests/conftest.py
"""
Configuration pytest : ajoute src/ au path Python pour que les imports
core.xxx, users.xxx, telegram_bot.xxx, web.xxx fonctionnent.
Injecte aussi un stub libsql pour permettre les tests sans base Turso.
"""

import os
import sys
import types

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_root, "src")
for _p in (_src, _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Stub libsql pour les tests sans base Turso
_libsql_stub = types.ModuleType("libsql")


def _connect(database: str = "", auth_token: str = "", **kwargs):
    if not database or not auth_token:
        raise RuntimeError(
            "TURSO_URL ou TURSO_TOKEN manquant. "
            "Impossible d'établir la connexion à la base."
        )
    raise RuntimeError("Connexion libSQL non disponible en environnement de test.")


class _Connection:
    def close(self):
        pass

    def execute(self, *args, **kwargs):
        raise RuntimeError("Connexion libSQL non disponible en environnement de test.")


_libsql_stub.connect = _connect
_libsql_stub.Connection = _Connection
sys.modules["libsql"] = _libsql_stub
