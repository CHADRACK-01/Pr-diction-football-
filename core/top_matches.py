# core/top_matches.py
from datetime import datetime, timezone, timedelta
from core.paris_builder import get_tous_pronostics_disponibles
from core.utils.logs import log_info, log_warning, log_error

TZ_KINSHASA = timezone(timedelta(hours=1))
SEUIL_CONFIANCE_MIN = 0.75

def _traduire_pari(home, away, label_dc):
    if label_dc == "1X": return f"<b>{home}</b> gagne ou fait match nul"
    if label_dc == "X2": return f"<b>{away}</b> gagne ou fait match nul"
    if label_dc == "12": return "Pas de match nul"
    return label_dc

def get_top_affiches(limite=10):
    try: matchs = get_tous_pronostics_disponibles()
    except Exception: return []
    if not matchs: return []
    top = [m for m in matchs if (m.get("reco_pct") or 0) >= SEUIL_CONFIANCE_MIN]
    if not top: return []
    top.sort(key=lambda x: x.get("reco_pct", 0), reverse=True)
    return top[:limite]

def formater_top_affiches(affiches, langue="fr", montrer_details=True):
    if not affiches: return "🏆 Aucun match sûr à 100% aujourd'hui."

    texte = f"👋 <b>Voici les matchs que je te conseille aujourd'hui.</b>\n"
    texte += f"J'ai analysé les statistiques et voici où tu as le plus de chances de gagner :\n\n"

    for i, m in enumerate(affiches, 1):
        try:
            home, away = m.get('home', '?'), m.get('away', '?')
            heure = "?"
            if m.get("heure"):
                try: heure = datetime.fromisoformat(str(m["heure"]).replace("Z", "+00:00")).astimezone(TZ_KINSHASA).strftime("%H:%M")
                except Exception: pass

            phrase_conseil = _traduire_pari(home, away, m.get('reco_label', '?'))
            texte += f"{i}. <b>{home} vs {away}</b> (à {heure})\n"
            
            if montrer_details:
                texte += f"   👉 Je te conseille de jouer : {phrase_conseil}\n"
                texte += f"   (J'ai <b>{round(m.get('reco_pct', 0) * 100, 1)}%</b> de certitude)\n\n"
            else:
                texte += f"   👉 Conseillé\n\n"
        except Exception: continue

    if not montrer_details: 
        texte += "⭐ <i>Passe Premium pour voir mes conseils détaillés et mes certitudes.</i>\n"
    return texte
