def calculer_cotes(prono, cotes_book=None):
    """
    Calcule les cotes implicites du bot et les compare au bookmaker.
    Retourne la meilleure option (Value Bet) ou une alternative si cote < 1.25.
    """
    # 1. Liste des options possibles
    options = [
        ("1X", prono['dc_1x']),
        ("X2", prono['dc_x2']),
        ("12", prono['dc_12']),
        ("Over 2.5", prono['over_25']),
        ("BTTS Oui", prono['btts_yes']),
        ("1 (Victoire Domicile)", prono['p_h']),
        ("2 (Victoire Extérieur)", prono['p_a'])
    ]
    
    # Trie par probabilité décroissante
    options.sort(key=lambda x: x[1], reverse=True)
    
    meilleure_option = None
    for label, proba in options:
        cote_bot = round(1 / proba, 2) if proba > 0 else 999
        
        # Si la cote est < 1.25, on l'ignore et on passe à l'option suivante
        if cote_bot < 1.25:
            continue
            
        # Si on a les cotes du bookmaker, on cherche la correspondance
        cote_book = None
        if cotes_book:
            if label == "1X" and cotes_book.get('h') and cotes_book.get('d'):
                cote_book = round(1 / (1/cotes_book['h'] + 1/cotes_book['d']), 2)
            elif label == "X2" and cotes_book.get('a') and cotes_book.get('d'):
                cote_book = round(1 / (1/cotes_book['a'] + 1/cotes_book['d']), 2)
            elif label == "12" and cotes_book.get('h') and cotes_book.get('a'):
                cote_book = round(1 / (1/cotes_book['h'] + 1/cotes_book['a']), 2)
            elif label == "1 (Victoire Domicile)":
                cote_book = cotes_book.get('h')
            elif label == "2 (Victoire Extérieur)":
                cote_book = cotes_book.get('a')
        
        # 2. Détection du Value Bet (Cote Bot < Cote Bookmaker)
        is_value_bet = False
        if cote_book and cote_bot < cote_book:
            is_value_bet = True
            
        meilleure_option = {
            "label": label,
            "proba": proba,
            "cote_bot": cote_bot,
            "cote_book": cote_book,
            "is_value": is_value_bet
        }
        break # On s'arrête à la première option qui passe le filtre 1.25
        
    return meilleure_option

def formater_analyse_paris(prono, meilleure_option):
    """
    Génère un texte clair pour afficher la comparaison.
    """
    if not meilleure_option:
        return None
        
    label = meilleure_option['label']
    proba = round(meilleure_option['proba'] * 100, 1)
    cote_bot = meilleure_option['cote_bot']
    cote_book = meilleure_option['cote_book']
    
    texte = f"🎯 **Paris recommandé : {label}**\n"
    texte += f"📊 Probabilité Bot : {proba}%\n"
    texte += f"🤖 Cote Bot : {cote_bot}\n"
    
    if cote_book:
        texte += f"🏢 Cote Bookmaker : {cote_book}\n"
        if meilleure_option['is_value']:
            texte += f"🔥 **VALUE BET DÉTECTÉ !** (Le bookmaker sous-estime ce pari)\n"
        else:
            texte += f"⚠️ Pas de valeur (Le bookmaker est plus optimiste)\n"
    else:
        texte += f"🏢 Cote Bookmaker : Indisponible\n"
        
    return texte
