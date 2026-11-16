# ai_dev/agent.py
import os
import json
import time
import requests
from core.utils.logs import log_info, log_error, log_warning

FICHIERS_INTERDITS = []  # Mode TEST : tout est autorisé

PROMPT_SYSTEME = """Tu es le développeur principal d'un bot Telegram de pronostic football en Python.
Tu reçois une demande de modification. Tu dois renvoyer UNIQUEMENT un objet JSON valide avec ce format exact :
{
  "explication": "Ce que tu vas faire (en français, simple)",
  "code_complet": "Le code Python complet du fichier après modification"
}
RÈGLES STRICTES :
- Ne touche JAMAIS aux paiements, aux mots de passe ou aux clés API.
- Le code doit être du Python valide, indenté correctement.
- Tu dois intégrer tes modifications dans le code existant fourni.
- Ne rajoute pas de blocs Markdown (```python) dans la clé "code_complet", juste le code brut.
"""

def _lire_fichier(chemin):
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log_error(f"Impossible de lire {chemin}", "AI_DEV", exception=e)
        return None

def _ecrire_fichier_test(chemin, contenu):
    chemin_test = chemin.replace(".py", "_test.py")
    try:
        with open(chemin_test, "w", encoding="utf-8") as f:
            f.write(contenu)
        return chemin_test
    except Exception as e:
        log_error(f"Impossible d'écrire {chemin_test}", "AI_DEV", exception=e)
        return None

# =========================================================
# GOOGLE GEMINI (IA PRINCIPALE) - Avec Retry sur 503
# =========================================================
def _appeler_google(instruction, contenu_actuel):
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return {"erreur": "Clé GOOGLE_AI_API_KEY manquante."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt_complet = f"{PROMPT_SYSTEME}\n\nCode actuel:\n```python\n{contenu_actuel}\n```\n\nDemande : {instruction}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_complet}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    # On tente 2 fois (retry) si Google est surchargé (503)
    for tentative in range(2):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=90)
            if res.status_code == 200:
                data = res.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                content = content.strip()
                if content.startswith("```json"): content = content[7:]
                if content.endswith("```"): content = content[:-3]
                return json.loads(content)
            
            if res.status_code == 503 and tentative == 0:
                log_warning("Google surchargé (503). Nouvelle tentative dans 3s...", "AI_DEV")
                time.sleep(3)
                continue
                
            log_warning(f"Google a échoué (code {res.status_code})", "AI_DEV")
            break # On sort de la boucle si c'est une autre erreur
        except Exception as e:
            log_error(f"Exception Google: {str(e)}", "AI_DEV", exception=e)
            break

    return {"erreur": "Google indisponible (503) ou timeout."}

# =========================================================
# GROQ (FALLBACK) - Modèle corrigé
# =========================================================
def _appeler_groq(instruction, contenu_actuel):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"erreur": "Clé GROQ_API_KEY manquante."}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-120b",  # Le modèle correct
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": f"Code actuel:\n```python\n{contenu_actuel}\n```\n\nDemande : {instruction}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=90)
        if res.status_code != 200:
            log_warning(f"Groq a échoué (code {res.status_code}) : {res.text[:200]}", "AI_DEV")
            return {"erreur": f"Groq HTTP {res.status_code}"}
        
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        log_warning(f"Exception Groq: {str(e)}", "AI_DEV")
        return {"erreur": "Erreur réseau Groq"}

# =========================================================
# LOGIQUE DE FALLBACK
# =========================================================
def demander_a_ia(instruction_utilisateur, contenu_actuel):
    log_info("Tentative avec Google Gemini...", "AI_DEV")
    reponse = _appeler_google(instruction_utilisateur, contenu_actuel)
    
    if "erreur" not in reponse and "code_complet" in reponse:
        log_info("Succès avec Google Gemini.", "AI_DEV")
        return reponse
        
    log_warning("Google a échoué. Bascule sur Groq...", "AI_DEV")
    reponse_fallback = _appeler_groq(instruction_utilisateur, contenu_actuel)
    
    if "erreur" not in reponse_fallback and "code_complet" in reponse_fallback:
        log_info("Succès avec Groq.", "AI_DEV")
        return reponse_fallback
        
    log_error("Les deux IA ont échoué.", "AI_DEV")
    return {"erreur": "Les deux IA ont échoué. Réessaie dans quelques instants."}

# =========================================================
# FONCTION PRINCIPALE
# =========================================================
def preparer_mise_a_jour(chemin_fichier, instruction):
    log_info(f"Demande IA : {instruction} sur {chemin_fichier}", "AI_DEV")

    contenu_actuel = _lire_fichier(chemin_fichier)
    if contenu_actuel is None:
        return False, "❌ Fichier introuvable.", None, None

    reponse = demander_a_ia(instruction, contenu_actuel)
    
    if "erreur" in reponse:
        return False, f"❌ {reponse['erreur']}", None, None

    explication = reponse.get("explication", "Aucune explication fournie.")
    nouveau_code = reponse.get("code_complet", "")

    if not nouveau_code or len(nouveau_code) < 50:
        return False, "❌ L'IA a renvoyé un code vide ou incomplet.", None, None

    chemin_test = _ecrire_fichier_test(chemin_fichier, nouveau_code)
    if not chemin_test:
        return False, "❌ Impossible de sauvegarder le code de test.", None, None

    return True, explication, chemin_test, nouveau_code
