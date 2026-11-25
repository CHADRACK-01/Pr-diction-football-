# core/jeu_responsable.py
"""
Mention de jeu responsable ajoutée aux bulletins de pronostics.

Activée uniquement si l'interrupteur « jeu_responsable » est actif
(panneau admin 🔧 Features). Désactivée par défaut : sans activation,
le message renvoyé est strictement identique à celui reçu.
"""
from core.utils.logs import log_warning
from core.administration.feature_flags import est_active

FEATURE_ID = "jeu_responsable"

MENTION_HTML = (
    "\n\n🔞 <i>Jeu responsable : ce bot donne des estimations, "
    "pas des certitudes. Aucun pronostic ne garantit un gain. "
    "Ne mise que ce que tu peux te permettre de perdre. "
    "Si le jeu devient un problème, arrête et parles-en à un proche.</i>"
)


def _est_active():
    try:
        return bool(est_active(FEATURE_ID))
    except Exception as e:
        # En cas de doute (base indisponible), on ne modifie pas le message
        log_warning(
            message="Interrupteur jeu_responsable illisible : mention non ajoutée",
            module="JEU_RESPONSABLE",
            exception=e,
        )
        return False


def ajouter_mention(texte_html):
    """Retourne le texte avec la mention si l'interrupteur est actif, sinon le texte inchangé."""
    if not texte_html or not _est_active():
        return texte_html
    return texte_html + MENTION_HTML
