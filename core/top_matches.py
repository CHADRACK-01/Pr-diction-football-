# core/top_matches.py
from datetime import datetime, timezone, timedelta
from core.paris_builder import get_tous_pronostics_disponibles
from core.utils.logs import log_info, log_warning, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))
SEUIL_CONFIANCE_MIN = 0.75

def get_top_affiches(limite=10):
    """Récupère les matchs où l'IA a une confiance >= 75%."""
    try:
        matchs = get_tous_pronostics_disponibles()
    except Exception as e:
        log_error("Erreur récupération top", "TOP", exception=e)
        return []
    if not matchs: return []
    
    # On ne garde que les matchs avec une forte confiance
    top = [m for m in matchs if (m.get("reco_pct") or 0) >= SEUIL_CONFIANCE_MIN]
    if not top: return []
    
    # On trie du plus sûr au moins sûr
    top.sort(key=lambda x: x.get("reco_pct", 0), reverse=True)
    return top[:limite]

def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    """Affiche les Top Affiches avec une explication claire."""
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    if not affiches: 
        return "🏆 Aucune affiche à fort potentiel aujourd'hui."

    texte = f"🎯 **TOP AFFICHES DU JOUR - {date_str}**\n"
    texte += "━━━━━━━━━━━━━━━━━━━━\n"
    texte += "💡 _Ces matchs sont sélectionnés car l'IA a une confiance **supérieure à 75%** sur le résultat (Pari Sûr)._\n\n"

    for i, m in enumerate(affiches, 1):
        try:
            texte += f"{i}. **{m.get('home', '?')}** vs **{m.get('away', '?')}**\n"
            texte += f"🏆 {m.get('nom_competition', '?')}\n"
            
            if montrer_details:
                p_h = m.get('p_h', 0.33)
                p_d = m.get('p_d', 0.33)
                p_a = m.get('p_a', 0.33)
                reco_pct = m.get("reco_pct", 0)
                reco_label = m.get('reco_label', '?')

                # Détail des probabilités
                texte += f"🏆 **Victoire {m['home']} :** {round(p_h*100)}%\n"
                texte += f"🤝 **Match Nul :** {round(p_d*100)}%\n"
                texte += f"✈️ **Victoire {m['away']} :** {round(p_a*100)}%\n"
                
                # La recommandation principale (Le fameux "Pari Sûr")
                texte += f"🛡️ **Recommandation (Double Chance) : {reco_label}**\n"
                texte += f"   └─ Confiance de l'IA : **{round(reco_pct * 100, 1)}%** ✅\n"
                
                # Les autres marchés
                texte += f"🎯 **Les 2 marquent :** {round(m.get('btts', 0.5) * 100, 1)}%\n"
                texte += f"🥅 **Plus de 2.5 buts :** {round(m.get('over_25', 0.5) * 100, 1)}%\n"
            else:
                texte += f"🎯 Reco : {m.get('reco_label', '?')}\n"
            texte += "\n"
        except Exception: continue

    if not montrer_details: 
        texte += "━━━━━━━━━━━━━━━━━━━━\n⭐ _Passe Premium pour voir les probabilités détaillées et l'analyse des cotes._\n"
    
    return texte
