# telegram_bot/features_handlers.py
"""
Handlers Telegram pour les fonctionnalités "décor" (stubs).

Ce module enregistre des commandes Telegram qui exposent chaque fonctionnalité
du catalogue core/catalogue_fonctionnalites.py. Chaque commande appelle le
stub associé et affiche un message indiquant que la fonctionnalité est
en cours d'implémentation.

À compléter : remplacer les appels aux stubs par la logique réelle une fois
chaque fonctionnalité implémentée.
"""

from core.utils.logs import log_info, log_warning
from core.catalog.catalogue_fonctionnalites import obtenir_catalogue

try:
    from telebot.types import Message
except Exception:
    Message = object  # type: ignore


def _formater_reponse_feature(feature_id: int, resultat: dict) -> str:
    """Formate la réponse d'une feature pour affichage Telegram."""
    statut = resultat.get("status", "a_implanter")
    message = resultat.get("message", "Aucun message")
    dependances = resultat.get("dependances", [])

    lignes = [
        f"🔧 <b>Fonctionnalité #{feature_id}</b>",
        f"<b>Statut :</b> {statut}",
        f"<b>Message :</b> {message}",
    ]
    if dependances:
        lignes.append(f"<b>Dépendances :</b> {', '.join(dependances)}")
    lignes.append("")
    lignes.append("⚠️ Cette fonctionnalité est en cours d'implémentation.")
    lignes.append("Contactez l'administrateur pour plus d'informations.")
    return "\n".join(lignes)


def enregistrer_features_handlers(bot) -> None:
    """
    Enregistre tous les handlers de fonctionnalités sur le bot Telegram.

    Chaque fonctionnalité du catalogue reçoit une commande /f{id}
    (ex: /f2 pour le détecteur de value bet).
    """
    catalogue = obtenir_catalogue()

    for feature_id_str, info in catalogue.items():
        feature_id = int(feature_id_str)
        stub_func = _resoudre_stub(feature_id)

        def make_handler(fid, fstub):
            def handler(message: Message):
                log_info(
                    f"Commande /f{fid} appelée par {message.from_user.id}",
                    "FEATURES_HANDLERS",
                )
                try:
                    resultat = fstub()
                except Exception as e:
                    log_warning(
                        f"Erreur dans le stub de la feature #{fid}",
                        "FEATURES_HANDLERS",
                        exception=e,
                    )
                    resultat = {
                        "status": "erreur",
                        "message": f"Erreur lors de l'exécution : {e}",
                        "dependances": [],
                    }
                texte = _formater_reponse_feature(fid, resultat)
                try:
                    bot.reply_to(message, texte, parse_mode="HTML")
                except Exception as e:
                    log_warning(
                        f"Impossible d'envoyer la réponse /f{fid}",
                        "FEATURES_HANDLERS",
                        exception=e,
                    )

            return handler

        commande = f"f{feature_id}"
        try:
            bot.register_message_handler(
                make_handler(feature_id, stub_func),
                commands=[commande],
                pass_chat=True,
            )
        except Exception as e:
            log_warning(
                f"Impossible d'enregistrer la commande /f{feature_id}",
                "FEATURES_HANDLERS",
                exception=e,
            )



def _resoudre_stub(feature_id: int):
    """
    Résout la fonction stub associée à un ID de fonctionnalité.

    Retourne un stub par défaut. Pour câbler une fonctionnalité spécifique,
    ajoutez une entrée dans le dictionnaire _MAPPING ci-dessous.
    """
    def _stub_par_defaut(*args, **kwargs):
        return {
            "status": "a_implanter",
            "feature_id": feature_id,
            "libelle": f"Fonctionnalité #{feature_id}",
            "message": (
                "À implémenter : créer le stub dans core/features/"
                " et l'enregistrer dans _MAPPING"
            ),
            "dependances": [],
        }
    return _stub_par_defaut