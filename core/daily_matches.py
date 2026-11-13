# core/daily_matches.py
from datetime import datetime, timezone, timedelta
from core.ml_model import global_model_data
from core.prediction import predire_match
from core.api.orchestrator import collecter_tous_les_matchs
from core.utils.logs import log_info, log_warning, log_error
from config import CHAMPIONNATS, INFOS_COMPETITIONS, MAPPING_COMPETITIONS

TZ_KINSHASA = timezone(timedelta(hours=1))

def _normaliser(nom):
    # (Garde ton dictionnaire de normalisation existant ici)
    return nom 

def _charger_modele_si_necessaire():
    if global_model_data.get("models") is not None: return True
    try:
        from core.ml_model import charger_et_entrainer
        return charger_et_entrainer()
    except Exception as e:
        log_error("Erreur chargement modèle", "MATCHS", exception=e)
        return False

def get_matchs_du_jour():
    if not _charger_modele_si_necessaire(): return []
    try:
        matchs_bruts = collecter_tous_les_matchs()
    except Exception as e:
        log_error("Erreur collecte", "MATCHS", exception=e)
        return []
    if not matchs_bruts: return []

    matchs_trouves = []
    for m in matchs_bruts:
        try:
            home = _normaliser(m.get("home", ""))
            away = _normaliser(m.get("away", ""))
            competition_code = m.get("competition", "default")
            if not home or not away: continue
            
            competition_reelle = m.get("competition_reelle") or MAPPING_COMPETITIONS.get(competition_code, competition_code)
            try:
                prono = predire_match(home, away, competition=competition_reelle, cotes_book=m.get("cotes_book"))
            except Exception: continue
            if not isinstance(prono, dict) or "erreur" in prono: continue

            dc_1x = float(prono.get("dc_1x", 0.5))
            dc_x2 = float(prono.get("dc_x2", 0.5))
            dc_12 = float(prono.get("dc_12", 0.5))
            meilleure = max([("1X", dc_1x), ("X2", dc_x2), ("12", dc_12)], key=lambda x: x[1])

            matchs_trouves.append({
                "competition": competition_code,
                "nom_competition": CHAMPIONNATS.get(competition_code, competition_code),
                "heure": m.get("heure"),
                "home": home, "away": away,
                "p_h": float(prono.get("p_h", 0.33)),
                "p_d": float(prono.get("p_d", 0.33)),
                "p_a": float(prono.get("p_a", 0.33)),
                "dc_label": meilleure[0],
                "dc_pct": float(meilleure[1]),
                "btts": float(prono.get("btts_yes", 0.5)),
                "over_25": float(prono.get("over_25", 0.5)),
            })
        except Exception: continue

    matchs_trouves.sort(key=lambda x: (x.get("heure") or "", -x["dc_pct"]))
    return matchs_trouves

def formater_matchs_du_jour(matchs, langue="fr", est_premium=False, nb_max=None):
    date_str = datetime.now(TZ_KINSHASA).strftime("%d/%m/%Y")
    if not matchs: return f"📅 Aucun match disponible."
    if nb_max: matchs = matchs[:nb_max]

    jours = {}
    for m in matchs:
        if not m.get("heure"): continue
        try:
            dt = datetime.fromisoformat(str(m["heure"]).replace("Z", "+00:00")).astimezone(TZ_KINSHASA)
            jour_key = dt.strftime("%A %d/%m/%Y")
            jours.setdefault(jour_key, []).append(m)
        except Exception: continue

    if not jours: return "📅 Aucun match valide."

    texte = f"📅 **PROGRAMME DES MATCHS**\nDu {date_str}\n\n"
    jours_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}

    for jour_label in sorted(jours.keys()):
        matchs_jour = jours[jour_label]
        jour_trad = jours_fr.get(jour_label.split(" ")[0], "")
        date_part = jour_label.split(" ", 1)[1] if " " in jour_label else ""
        texte += "━━━━━━━━━━━━━━━━━━━━\n"
        texte += f"📅 **{jour_trad} {date_part}**\n"
        texte += "━━━━━━━━━━━━━━━━━━━━\n\n"
        matchs_jour.sort(key=lambda x: x.get("heure") or "")

        for m in matchs_jour:
            try:
                heure = datetime.fromisoformat(str(m["heure"]).replace("Z", "+00:00")).astimezone(TZ_KINSHASA).strftime("%H:%M")
            except Exception: heure = "?"
            
            info = INFOS_COMPETITIONS.get(m.get("nom_competition"), {})
            emoji_pays = info.get("emoji", "🏆")
            
            texte += f"⚽ **{m['home']}** 🆚 **{m['away']}**\n"
            texte += f"   🕐 {heure} | 🏆 {m['nom_competition']} {emoji_pays}\n"
            
            if est_premium:
                # Explication claire pour un débutant
                texte += f"   🏆 **Victoire {m['home']} :** {round(m['p_h']*100)}%\n"
                texte += f"   🤝 **Match Nul :** {round(m['p_d']*100)}%\n"
                texte += f"   ✈️ **Victoire {m['away']} :** {round(m['p_a']*100)}%\n"
                texte += f"   🛡️ **Pari Sûr (Double Chance) :** {m['dc_label']} ({round(m['dc_pct']*100,1)}%)\n"
                texte += f"   🎯 **Les 2 marquent :** {round(m['btts']*100,1)}%\n"
                texte += f"   🥅 **Plus de 2.5 buts :** {round(m['over_25']*100,1)}%\n"
            texte += "\n"

    if not est_premium:
        texte += "━━━━━━━━━━━━━━━━━━━━\n⭐ _Passe Premium pour voir les pronostics et les probabilités de chaque match._\n"
    return texte
