# ai_dev/tester.py
"""
Testeur automatique de code.
Vérifie que le code généré par l'IA est du Python valide (syntaxe et compilation).
"""

import ast
import py_compile
import os
from core.utils.logs import log_info, log_error

def tester_code(chemin_fichier_test):
    """
    Teste le fichier généré par l'IA.
    Retourne (succes: bool, message: str).
    """
    log_info(f"Début des tests sur {chemin_fichier_test}", "AI_TESTER")

    # Vérification 1 : Le fichier existe-t-il ?
    if not os.path.exists(chemin_fichier_test):
        return False, "❌ Fichier de test introuvable."

    # Vérification 2 : Syntaxe pure (AST)
    try:
        with open(chemin_fichier_test, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
    except SyntaxError as e:
        log_error(f"Erreur de syntaxe détectée : {e}", "AI_TESTER")
        return False, f"❌ Erreur de syntaxe ligne {e.lineno} : {e.msg}"
    except Exception as e:
        log_error(f"Erreur de lecture AST : {e}", "AI_TESTER")
        return False, f"❌ Erreur de lecture : {str(e)}"

    # Vérification 3 : Compilation (crée un fichier .pyc temporaire)
    try:
        py_compile.compile(chemin_fichier_test, doraise=True)
    except py_compile.PyCompileError as e:
        log_error(f"Erreur de compilation détectée : {e}", "AI_TESTER")
        return False, f"❌ Erreur de compilation : {str(e)}"
    except Exception as e:
        log_error(f"Erreur inattendue lors de la compilation : {e}", "AI_TESTER")
        return False, f"❌ Erreur inattendue : {str(e)}"

    # Si on arrive ici, c'est que le code est syntaxiquement parfait
    log_info(f"✅ Tests réussis pour {chemin_fichier_test}", "AI_TESTER")
    return True, "✅ Tests de syntaxe et de compilation réussis."
