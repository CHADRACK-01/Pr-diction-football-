"""Analyseur statique en lecture seule pour le rapport d'audit."""
import ast
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".venv", "__pycache__", ".git", "node_modules", "backups_ia", "build", "dist"}


def fichiers_py():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".py"):
                chemin = os.path.join(base, f)
                yield chemin, os.path.relpath(chemin, ROOT).replace("\\", "/")


def nom_module(rel):
    if rel.endswith("/__init__.py"):
        return rel[: -len("/__init__.py")].replace("/", ".")
    return rel[:-3].replace("/", ".")


IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))", re.M)


def imports_du_fichier(source):
    trouves = set()
    for m in IMPORT_RE.finditer(source):
        if m.group(1):
            trouves.add(m.group(1))
        else:
            for part in m.group(2).split(","):
                part = part.strip().split(" as ")[0].strip()
                if part:
                    trouves.add(part)
    # imports dynamiques du type importlib.import_module("core.x")
    for m in re.finditer(r"import_module\(\s*[\"']([\w.]+)[\"']", source):
        trouves.add(m.group(1))
    return trouves


def main():
    modules = {}
    sources = {}
    lignes = {}
    for chemin, rel in fichiers_py():
        module = nom_module(rel)
        modules[module] = rel
        try:
            with open(chemin, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError:
            continue
        sources[module] = src
        lignes[module] = src.count("\n")

    # index des imports
    importeurs = defaultdict(set)
    for module, src in sources.items():
        for imp in imports_du_fichier(src):
            importeurs[imp].add(module)
            # sous-module implicite : from core import x  ->  core.x
            for connu in modules:
                if connu.startswith(imp + "."):
                    parent = imp
                    if connu.count(".") == parent.count(".") + 1:
                        importeurs[imp].add(module)

    def est_importe(module):
        if module in importeurs:
            return True
        # importé via un parent (from core.data import x)
        morceaux = module.split(".")
        for i in range(1, len(morceaux)):
            parent = ".".join(morceaux[:i])
            reste = morceaux[i]
            if parent in importeurs and parent + "." + reste == module:
                return True
        return False

    racines = {"test_" + p.stem for p in []}  # placeholder
    test_modules = {m for m in modules if m.startswith("tests.") or m == "tests"}

    orphelins = []
    for module, rel in sorted(modules.items()):
        if module.startswith("tests") or module == "conftest" or rel.startswith("tests/"):
            continue
        if not est_importe(module):
            orphelins.append((module, lignes.get(module, 0)))

    print("=== MODULES JAMAIS IMPORTES (hors tests) ===")
    print(f"total : {len(orphelins)} / {len(modules)}")
    for module, n in sorted(orphelins, key=lambda x: -x[1]):
        print(f"  {n:5d}  {module}")

    print()
    print("=== MARQUEURS DE STUB PAR DOSSIER ===")
    marq = Counter()
    tous = Counter()
    for module, src in sources.items():
        dossier = module.split(".")[0] if "." in module else "(racine)"
        for motif in ('"a_implanter"', "'a_implanter'", "TODO", "NotImplementedError", "pass  #"):
            c = src.count(motif)
            if c:
                marq[(dossier, motif)] += c
                tous[dossier] += c
    for dossier, n in tous.most_common():
        detail = {k[1]: v for k, v in marq.items() if k[0] == dossier}
        print(f"  {dossier:16s} {n:5d}  {detail}")

    print()
    print("=== DOUBLONS PLAT / SOUS-PAQUET DANS core/ ===")
    plats = {m.split(".")[1] for m in modules if m.startswith("core.") and m.count(".") == 1}
    sous = defaultdict(list)
    for m in modules:
        if m.startswith("core.") and m.count(".") == 2:
            sous[m.split(".")[2]].append(m)
    doublons = sorted(set(plats) & set(sous))
    print(f"basenames presents en plat ET en sous-paquet : {len(doublons)}")
    for d in doublons:
        print(f"  core/{d}.py  <->  {', '.join(sous[d])}")

    print()
    print("=== FONCTIONS SANS DOCSTRING (top 20 fichiers) ===")
    stats = []
    for module, src in sources.items():
        try:
            arbre = ast.parse(src)
        except SyntaxError:
            continue
        total = sans = 0
        for noeud in ast.walk(arbre):
            if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                total += 1
                if not ast.get_docstring(noeud):
                    sans += 1
        if total:
            stats.append((sans, total, module))
    for sans, total, module in sorted(stats, key=lambda x: -x[0])[:20]:
        print(f"  {sans:4d}/{total:4d} sans docstring  {module}")

    print()
    print("=== FICHIERS SANS AUCUN TEST REFERENCHE ===")
    testes = set()
    for module, src in sources.items():
        if module.startswith("tests"):
            for imp in imports_du_fichier(src):
                testes.add(imp)
    non_testes = []
    for module, src in sources.items():
        if module.startswith("tests") or "test" in module:
            continue
        if lignes.get(module, 0) < 30:
            continue
        if not any(t == module or module.startswith(t + ".") for t in testes):
            non_testes.append((lignes[module], module))
    print(f"modules >30 lignes jamais importes par un test : {len(non_testes)}")
    for n, module in sorted(non_testes, reverse=True)[:25]:
        print(f"  {n:5d}  {module}")


if __name__ == "__main__":
    main()
