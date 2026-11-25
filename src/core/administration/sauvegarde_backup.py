"""Sauvegarde locale sécurisée des données Turso/sqlite, sans stockage secret."""

import csv
import io
import json
from datetime import datetime


def exporter_tables_csv(tables):
    """Exporte des lignes SQL déjà récupérées en plusieurs sections CSV."""
    export = {}
    for nom_table, lignes in tables.items():
        tampon = io.StringIO()
        lignes = list(lignes)
        if lignes:
            colonnes = lignes[0].keys()
            writer = csv.DictWriter(tampon, fieldnames=colonnes)
            writer.writeheader()
            writer.writerows(lignes)
        export[nom_table] = tampon.getvalue()
    return export


def creer_manifest_backup(tables, base="turso"):
    return {
        "base": base,
        "created_at": datetime.now().isoformat(),
        "tables": {nom: len(lignes) for nom, lignes in tables.items()},
        "format": "json",
    }


def serialiser_backup(tables):
    """Produit un JSON sérialisable avant chiffrement ou envoi Telegram."""
    manifest = creer_manifest_backup(tables)
    contenu = {nom: [dict(ligne) for ligne in lignes] for nom, lignes in tables.items()}
    return json.dumps({"manifest": manifest, "contenu": contenu}, ensure_ascii=False, default=str)
