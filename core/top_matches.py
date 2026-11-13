# core/top_matches.py
from datetime import datetime, timezone, timedelta
from core.paris_builder import get_tous_pronostics_disponibles
from core.utils.logs import log_info, log_warning, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))
SEUIL_CONFIANCE_MIN = 0.75

def get_top_affiches(limite=10):
    try:
        matchs = get_tous_pronostics_disponibles()
    except Exception as e:
        log_error("Erreur récupération top", "TOP", exception=e)
        return []
    if not matchs: return []
    
    top = [m for m in matchs if (m.get("reco_pct") or 0) >= SEUIL_CONFIANCE_MIN]
    if not top: return []
    
    top.sort(key=lambda x: x.get("reco_pct", 0), reverse=True)
    return top[:limite]

def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    if not affiches: 
        return "🏆 Aucun match sûr à 100% aujourd'hui."

    texte = f"🎯 **LES PARIS LES PLUS SÛRS DU JOUR**\n\n"

    for i, m in enumerate(affiches, 1):
        try:
            home = m.get('home', '?')
            away = m.get('away', '?')
            heure = "?"
            if m.get("heure"):
                try:
                    heure = datetime.fromisoformat(str(m["heure"]).replace("Z", "+00:00")).astimezone(TZ_KINSHASA).strftime("%H:%M")
                except Exception: pass

            texte += f"{i}. **{home} vs {away}**\n"
            
            if montrer_details:
                p_h = m.get('p_h', 0.33)
                p_d = m.get('p_d', 0.33)
                p_a = m.get('p_a', 0.33)
                reco_pct = m.get("reco_pct", 0)
                reco_label = m.get('reco_label', '?')
                
                # On met l'essentiel : L'heure, la reco, la confiance
                texte += f"   🕐 {heure} | 🛡️ **{reco_label}** ({round(reco_pct * 100, 1)}%)\n"
                
                # On résume le 1N2 sur une seule ligne
                texte += f"   📊 1:{round(p_h*100)}% / N:{round(p_d*100)}% / 2:{round(p_a*100)}%\n"
            else:
                texte += f"   🎯 Reco : {m.get('reco_label', '?')}\n"
            
            texte += "\n"
        except Exception: continue

    if not montrer_details: 
        texte += "_Passe Premium pour voir l'heure et les probabilités._\n"
    
    return texte
