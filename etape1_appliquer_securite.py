# =====================================================================
# ÉTAPE 1 — Appliquer les corrections de sécurité au projet
#
# MODE D'EMPLOI (le plus simple) :
#   1. Place CE fichier à la RACINE de ton dépôt GitHub (le dossier qui
#      contient app.py, config.py, core/, users/...).
#   2. Dans un terminal, placé dans ce dossier, lance :
#        python etape1_appliquer_securite.py
#   3. Le script modifie app.py, ai_dev/agent.py et config.py.
#   4. Teste en local (voir etape1c_tester_webhook.py), puis envoie sur GitHub.
#
# Le chemin est détecté automatiquement : le script travaille dans le
# dossier où il se trouve. Rien à modifier.
# =====================================================================
import os
PROJET = os.path.dirname(os.path.abspath(__file__))

import os
import shutil
import sys

def chemin(relatif):
    return os.path.join(PROJET, *relatif.split("/"))

def lire(relatif):
    with open(chemin(relatif), "rb") as f:
        return f.read().decode("utf-8")

def ecrire(relatif, texte_lf, crlf):
    if crlf:
        texte_lf = texte_lf.replace("\n", "\r\n")
    with open(chemin(relatif), "wb") as f:
        f.write(texte_lf.encode("utf-8"))

def sauvegarder(relatif):
    src = chemin(relatif)
    if not os.path.exists(src + ".bak"):
        shutil.copy2(src, src + ".bak")

def remplacer(texte, ancien, nouveau, nom):
    if nouveau in texte:
        print(f"   · {nom} : déjà appliqué, on passe.")
        return texte
    if texte.count(ancien) != 1:
        sys.exit(f"ERREUR sur {nom} : texte d'origine introuvable ou en double. Rien n'a été modifié dans ce fichier.")
    print(f"   ✓ {nom} : appliqué.")
    return texte.replace(ancien, nouveau)

def verifier_projet():
    if not os.path.isfile(chemin("app.py")):
        sys.exit(f"ERREUR : pas de app.py dans {PROJET}. Place ce script à la racine du dépôt (là où se trouve app.py).")

# =====================================================================
verifier_projet()
print("== 1/3 app.py (webhook + debug_model) ==")
rel = "app.py"
sauvegarder(rel)
s = lire(rel).replace("\r\n", "\n")

s = remplacer(s,
'''@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        _initialiser_bdd_si_necessaire()''',
'''@app.route("/webhook", methods=["POST"])
def webhook():
    # Telegram envoie le secret dans l'en-tête X-Telegram-Bot-Api-Secret-Token.
    # Le token du bot n'est plus dans l'URL, donc il n'apparaît plus dans les logs.
    secret_attendu = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    secret_recu = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret_attendu or not hmac.compare_digest(secret_attendu, secret_recu):
        log_warning(
            message="Webhook refusé : secret invalide ou absent",
            module="FLASK",
            extra={"ip": request.remote_addr},
        )
        return "Forbidden", 403

    try:
        _initialiser_bdd_si_necessaire()''',
"route webhook")

s = remplacer(s,
'''@app.route("/debug_model")
def debug_model():''',
'''@app.route("/debug_model")
@admin_required
def debug_model():''',
"debug_model protégé")

s = remplacer(s, "import time\nimport threading\n", "import time\nimport hmac\nimport threading\n", "import hmac")
ecrire(rel, s, crlf=True)

print("== 2/3 ai_dev/agent.py (clé Gemini + fichiers interdits) ==")
rel = "ai_dev/agent.py"
sauvegarder(rel)
s = lire(rel)
s = remplacer(s,
'FICHIERS_INTERDITS = []',
'''# Fichiers que l'IA ne doit JAMAIS modifier automatiquement.
FICHIERS_INTERDITS = [
    "config.py",
    "app.py",
    "core/paiement_auto.py",
    "core/payments.py",
    "core/securite.py",
    "users/paiements.py",
    "users/db.py",
    "telegram_bot/payment_handlers.py",
    "telegram_bot/admin/actions.py",
]''',
"liste FICHIERS_INTERDITS")
s = remplacer(s,
'''    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}''',
'''    # Clé dans l'en-tête (et non dans l'URL) pour qu'elle n'apparaisse pas dans les logs.
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}''',
"clé Gemini dans l'en-tête")
ecrire(rel, s, crlf=False)

print("== 3/3 config.py (secret webhook) ==")
rel = "config.py"
sauvegarder(rel)
s = lire(rel)
s = remplacer(s,
'TOKEN = os.environ.get("TELEGRAM_TOKEN", "")',
'''TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
# Secret envoyé par Telegram dans l'en-tête X-Telegram-Bot-Api-Secret-Token
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")''',
"variable TELEGRAM_WEBHOOK_SECRET")
s = remplacer(s,
'''    if not CANAL_ID:
        problemes.append("CANAL_ID manquant ou invalide")''',
'''    if not CANAL_ID:
        problemes.append("CANAL_ID manquant ou invalide")
    if not MODE_TEST and not TELEGRAM_WEBHOOK_SECRET:
        problemes.append("TELEGRAM_WEBHOOK_SECRET manquant (requis pour le webhook)")''',
"vérification du secret au démarrage")
ecrire(rel, s, crlf=False)

print("\n== Vérification de la syntaxe ==")
import py_compile
for rel in ["app.py", "ai_dev/agent.py", "config.py"]:
    py_compile.compile(chemin(rel), doraise=True)
    print(f"   ✓ {rel} : syntaxe OK")
print("\nTerminé. Les fichiers d'origine sont sauvegardés avec l'extension .bak.")
print("Prochaine étape : etape1b_enregistrer_webhook.py.")
