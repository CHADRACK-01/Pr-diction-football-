# =====================================================================
# ÉTAPE 1c — Tester le webhook (local ou Render)
#
# Place ce fichier n'importe où (par exemple à la racine du dépôt).
# Il envoie deux requêtes à ton bot :
#   - sans secret  -> le bot DOIT répondre 403 (refusé)
#   - avec secret  -> le bot DOIT répondre 200 (accepté)
#
# Lancement (PowerShell) :
#   $env:APP_URL="https://ton-app.onrender.com"
#   $env:TELEGRAM_WEBHOOK_SECRET="ton_secret"
#   python etape1c_tester_webhook.py
#
# Pour tester en local, mets APP_URL=http://127.0.0.1:10000 après avoir lancé
# le bot localement (python app.py ou gunicorn app:app).
# =====================================================================
import os
import sys
import json
import urllib.request
import urllib.error

APP_URL = os.environ.get("APP_URL", "").strip().rstrip("/")
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()

if not APP_URL or not SECRET:
    sys.exit("ERREUR : définis APP_URL et TELEGRAM_WEBHOOK_SECRET.")

URL = f"{APP_URL}/webhook"
CORPS = json.dumps({"update_id": 1}).encode("utf-8")  # update vide, sans effet pour l'utilisateur

def envoyer(entetes):
    req = urllib.request.Request(URL, data=CORPS, method="POST",
                                 headers={"Content-Type": "application/json", **entetes})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")[:100]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:100]
    except Exception as e:
        return None, f"connexion impossible : {e}"

ok = True

# Vérifie d'abord que le serveur répond
_code_test, _ = envoyer({})
if _code_test is None:
    sys.exit("ERREUR : le bot n'est pas joignable à l'adresse " + APP_URL +
             ".\nVérifie que le service Render est démarré (ou que ton bot tourne en local).")

print("1) Requête SANS secret (doit être refusée, 403)")
code, texte = envoyer({})
print(f"   réponse : {code} {texte!r}")
if code != 403:
    ok = False
    print("   ❌ ÉCHEC : le bot n'a pas refusé la requête sans secret.")
else:
    print("   ✅ OK")

print("2) Requête AVEC le bon secret (doit être acceptée, 200)")
code, texte = envoyer({"X-Telegram-Bot-Api-Secret-Token": SECRET})
print(f"   réponse : {code} {texte!r}")
if code != 200:
    ok = False
    print("   ❌ ÉCHEC : le bot n'a pas accepté le bon secret.")
else:
    print("   ✅ OK")

print("3) Requête avec un MAUVAIS secret (doit être refusée, 403)")
code, texte = envoyer({"X-Telegram-Bot-Api-Secret-Token": "mauvais_secret"})
print(f"   réponse : {code} {texte!r}")
if code != 403:
    ok = False
    print("   ❌ ÉCHEC")
else:
    print("   ✅ OK")

print("\nRÉSULTAT :", "tous les tests passent ✅" if ok else "des tests échouent ❌")
