# ai_dev/agent.py
"""
Agent IA Développeur.
Utilise Google Gemini (gemini-3.8-flash) en principal, et Groq (openai/gpt-oss-120b) en fallback.
Gère la création de nouveaux fichiers si le fichier cible n'existe pas.
"""

import os
import json
import time
import requests
from core.utils.logs import log_info, log_error, log_warning

# Mode TEST : Liste vide pour autoriser tous les fichiers
# Fichiers que l'IA ne doit JAMAIS modifier automatiquement.
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
]

PROMPT_SYSTEME = """Tu es le développeur principal d'un bot Telegram de pronostic football en Python.
Tu reçois une demande de modification. Tu dois renvoyer UNIQUEMENT un objet JSON valide avec ce format exact :
{
  "explication": "Ce que tu vas faire (en français, simple)",
  "code_complet": "Le code Python complet du fichier après modification (ou le nouveau fichier à créer)"
}
RÈGLES STRICTES :
- Ne touche JAMAIS aux paiements, aux mots de passe ou aux clés API (sauf si on te le demande explicitement).
- Le code doit être du Python valide, indenté correctement.
- Si le fichier existe déjà, intègre tes modifications dans le code existant fourni.
- Si le fichier n'existe pas encore, crée-le de zéro avec le code complet nécessaire.
- Ne rajoute pas de blocs Markdown (```python) dans la clé "code_complet", juste le code brut.
"""

def _lire_fichier(chemin):
    """
    Lit le contenu d'un fichier.
    Si le fichier n'existe pas, retourne une chaîne vide pour permettre la création.
    Si erreur de droits, retourne None.
    """
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Le fichier n'existe pas : on retourne une chaîne vide
        log_info(f"Fichier {chemin} introuvable. Il sera créé.", "AI_DEV")
        return ""
    except Exception as e:
        log_error(f"Impossible de lire {chemin}", "AI_DEV", exception=e)
        return None

def _ecrire_fichier_test(chemin, contenu):
    """Écrit le code généré dans un fichier de test temporaire."""
    chemin_test = chemin.replace(".py", "_test.py")
    try:
        # S'assurer que le dossier existe
        os.makedirs(os.path.dirname(chemin_test) or ".", exist_ok=True)
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

    # Clé dans l'en-tête (et non dans l'URL) pour qu'elle n'apparaisse pas dans les logs.
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    
    contexte_code = f"Code actuel du fichier :\n```python\n{contenu_actuel}\n```" if contenu_actuel else "Le fichier est nouveau, il n'existe pas encore."
    prompt_complet = f"{PROMPT_SYSTEME}\n\n{contexte_code}\n\nDemande : {instruction}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_complet}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

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
                
            log_warning(f"Google a échoué (code {res.status_code}) : {res.text[:200]}", "AI_DEV")
            break
        except Exception as e:
            log_error(f"Exception Google: {str(e)}", "AI_DEV", exception=e)
            break

    return {"erreur": "Google indisponible (503) ou timeout."}

# =========================================================
# GROQ (FALLBACK)
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
    
    contexte_code = f"Code actuel du fichier :\n```python\n{contenu_actuel}\n```" if contenu_actuel else "Le fichier est nouveau, il n'existe pas encore."
    
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": f"{contexte_code}\n\nDemande : {instruction}"}
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
    
    # Si contenu_actuel est None, c'est une vraie erreur (droits, etc.)
    # S'il est vide "", c'est que le fichier n'existait pas, c'est OK.
    if contenu_actuel is None:
        return False, "❌ Impossible de lire le fichier (problème de droits).", None, None

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
