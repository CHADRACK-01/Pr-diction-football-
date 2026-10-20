import json

def _scheduler_notifications():
    """Tâche de fond qui gère les envois automatiques."""
    print("Scheduler demarre...")
    
    # ⚠️ On charge l'état depuis un fichier pour survivre aux redémarrages
    etat_fichier = "/tmp/scheduler_state.json"
    try:
        with open(etat_fichier, "r") as f:
            etat = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        etat = {}

    while True:
        try:
            now = datetime.now(TZ_KINSHASA)
            jour_semaine = now.weekday()
            est_weekend = jour_semaine >= 5
            date_du_jour = now.strftime("%Y-%m-%d")

            # ⚠️ SÉCURITÉ : Si la valeur en BDD est du texte, on utilise 8 par défaut
            heure_notif_val = get_parametre("notif_heure", "8")
            if isinstance(heure_notif_val, str) and heure_notif_val.isdigit():
                heure_notif = int(heure_notif_val)
            elif isinstance(heure_notif_val, int):
                heure_notif = heure_notif_val
            else:
                heure_notif = 8

            # 1. Vérification des résultats de la veille (à 7h)
            if now.hour == 7 and now.minute < 5:
                if etat.get("derniere_verif_resultats") != date_du_jour:
                    print(f"Vérification des résultats du {date_du_jour}...")
                    from core.results_checker import verifier_resultats_veille
                    from core.canal_manager import publier_bilan_veille
                    bilan = verifier_resultats_veille()
                    if bilan.get('total', 0) > 0:
                        publier_bilan_veille(bot, bilan['texte'])
                    etat["derniere_verif_resultats"] = date_du_jour
                    with open(etat_fichier, "w") as f:
                        json.dump(etat, f)

            # 2. Notifications et Canal (à 8h)
            if now.hour == heure_notif and now.minute < 5:
                if etat.get("derniere_date_envoi") != date_du_jour:
                    print(f"Envoi des notifications du {date_du_jour}...")
                    _envoyer_notifications()
                    etat["derniere_date_envoi"] = date_du_jour
                    with open(etat_fichier, "w") as f:
                        json.dump(etat, f)
                    
                    if est_weekend:
                        print("Weekend : envoi des coupons...")
                        _envoyer_coupons_premium()
                        etat["derniere_date_coupons_weekend"] = date_du_jour
                        with open(etat_fichier, "w") as f:
                            json.dump(etat, f)
                        
                    if etat.get("derniere_date_canal") != date_du_jour:
                        from core.canal_manager import publier_matchs_sur_canal
                        publier_matchs_sur_canal(bot)
                        etat["derniere_date_canal"] = date_du_jour
                        with open(etat_fichier, "w") as f:
                            json.dump(etat, f)

            # 3. Coupons Semaine (à 10h)
            if not est_weekend and now.hour == 10 and now.minute < 5:
                if etat.get("derniere_date_coupons_semaine") != date_du_jour:
                    print(f"Envoi des coupons du {date_du_jour}...")
                    _envoyer_coupons_premium()
                    from core.canal_manager import publier_coupons_sur_canal
                    publier_coupons_sur_canal(bot)
                    etat["derniere_date_coupons_semaine"] = date_du_jour
                    with open(etat_fichier, "w") as f:
                        json.dump(etat, f)

            # 4. Teasing Canal (à 17h)
            if now.hour == 17 and now.minute < 5:
                if etat.get("derniere_date_teasing") != date_du_jour:
                    print(f"Publication du teasing sur le canal...")
                    from core.canal_manager import publier_teasing
                    publier_teasing(bot)
                    etat["derniere_date_teasing"] = date_du_jour
                    with open(etat_fichier, "w") as f:
                        json.dump(etat, f)

            # 5. Nettoyage automatique (à 3h)
            if now.hour == 3 and now.minute < 5:
                if etat.get("dernier_nettoyage") != date_du_jour:
                    print(f"Nettoyage auto du {date_du_jour}...")
                    from users import nettoyer_logs_anciens, nettoyer_paiements_anciens
                    nettoyer_logs_anciens(jours=30)
                    nettoyer_paiements_anciens(jours=90)
                    etat["dernier_nettoyage"] = date_du_jour
                    with open(etat_fichier, "w") as f:
                        json.dump(etat, f)

            time.sleep(60)
        except Exception as e:
            print(f"Erreur scheduler globale : {e}")
            time.sleep(60)
