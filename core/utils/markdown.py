def echapper_markdown(texte):
    """
    Échappe les caractères spéciaux du Markdown pour éviter l'erreur 
    'can't parse entities' de Telegram.
    """
    if not texte:
        return ""
    
    caracteres_dangereux = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in caracteres_dangereux:
        texte = texte.replace(char, f'\\{char}')
    
    return texte


def formater_proprement(texte):
    """
    Nettoie un texte pour qu'il soit sûr à envoyer sur Telegram.
    Garde les ** pour le gras.
    """
    if not texte:
        return ""
    
    texte_secu = texte.replace('**', '§§GRAS§§')
    texte_secu = echapper_markdown(texte_secu)
    texte_secu = texte_secu.replace('§§GRAS§§', '**')
    
    return texte_secu
