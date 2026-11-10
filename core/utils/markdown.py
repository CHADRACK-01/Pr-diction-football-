from core.utils.logs import log_error


def echapper_markdown(texte):
    """
    Échappe les caractères spéciaux du Markdown pour éviter l'erreur 
    'can't parse entities' de Telegram.
    """
    if not texte:
        return ""
    
    try:
        # ⚠️ On échappe d'abord le backslash, sinon on double les échappements
        texte = str(texte).replace('\\', '\\\\')
        
        caracteres_dangereux = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in caracteres_dangereux:
            texte = texte.replace(char, f'\\{char}')
        
        return texte
    except Exception as e:
        log_error("Erreur lors de l'échappement Markdown", "MARKDOWN", exception=e)
        return str(texte) if texte else ""


def formater_proprement(texte):
    """
    Nettoie un texte pour qu'il soit sûr à envoyer sur Telegram.
    Garde les ** pour le gras.
    """
    if not texte:
        return ""
    
    try:
        # Placeholder plus sûr : caractère nul (aucun nom d'équipe ne contient \x00)
        texte_secu = str(texte).replace('**', '\x00GRAS\x00')
        texte_secu = echapper_markdown(texte_secu)
        texte_secu = texte_secu.replace('\x00GRAS\x00', '**')
        
        return texte_secu
    except Exception as e:
        log_error("Erreur lors du formatage propre du texte", "MARKDOWN", exception=e)
        return str(texte) if texte else ""
