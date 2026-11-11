# core/utils/markdown.py
"""
Utilitaires Markdown pour Telegram.

Stratégie :
- `echapper_markdown_v2(texte)` : échappe tous les caractères réservés V2
- `formater_proprement(texte)` : garde les ** pour le gras, échappe le reste
- `envoyer_securise(bot, chat_id, texte, parse_mode)` : envoi avec fallback
"""

from core.utils.logs import log_error, log_warning

# Caractères réservés en MarkdownV2 (Telegram)
# Source : https://core.telegram.org/bots/api#markdownv2-style
_CARACTERES_V2 = [
    '\\', '_', '*', '[', ']', '(', ')', '~', '`', '>',
    '#', '+', '-', '=', '|', '{', '}', '.', '!'
]


def echapper_markdown_v2(texte: str) -> str:
    """Échappe les caractères réservés MarkdownV2."""
    if not texte:
        return ""
    try:
        texte = str(texte)
        # Backslash d'abord (sinon on double les échappements)
        texte = texte.replace('\\', '\\\\')
        for char in _CARACTERES_V2:
            if char == '\\':
                continue
            texte = texte.replace(char, f'\\{char}')
        return texte
    except Exception as e:
        log_error(
            message="Erreur lors de l'échappement MarkdownV2",
            module="MARKDOWN",
            exception=e,
            extra={"texte_preview": str(texte)[:200]},
        )
        return str(texte) if texte else ""


def echapper_markdown(texte: str) -> str:
    """
    Échappe pour MarkdownV1 (legacy).
    Garde la compatibilité avec les anciens handlers.
    """
    if not texte:
        return ""
    try:
        texte = str(texte).replace('\\', '\\\\')
        # V1 est moins strict : on échappe l'essentiel
        for char in ['_', '*', '[', ']', '`']:
            texte = texte.replace(char, f'\\{char}')
        return texte
    except Exception as e:
        log_error(
            message="Erreur lors de l'échappement Markdown V1",
            module="MARKDOWN",
            exception=e,
        )
        return str(texte) if texte else ""


def formater_proprement(texte: str) -> str:
    """
    Nettoie un texte pour Telegram MarkdownV1 :
    - Préserve les ** pour le gras
    - Échappe le reste
    """
    if not texte:
        return ""
    try:
        # Placeholder pour préserver **gras**
        placeholder = '\x00GRAS\x00'
        texte_secu = str(texte).replace('**', placeholder)
        texte_secu = echapper_markdown(texte_secu)
        texte_secu = texte_secu.replace(placeholder, '**')
        return texte_secu
    except Exception as e:
        log_error(
            message="Erreur lors du formatage propre",
            module="MARKDOWN",
            exception=e,
            extra={"texte_preview": str(texte)[:200]},
        )
        return str(texte) if texte else ""


def envoyer_securise(bot, chat_id, texte, parse_mode="Markdown",
                     reply_markup=None, context=None):
    """
    Envoie un message avec fallback automatique :
    1. Essaie avec le parse_mode demandé
    2. Si échec → essaie sans parse_mode
    3. Si échec → log_error et retourne False

    Retourne True si succès, False sinon.
    """
    from core.utils.logs import log_error

    if not texte:
        return False

    # Découpage si trop long
    limite = 4000
    morceaux = [texte[i:i + limite] for i in range(0, len(texte), limite)]

    for i, morceau in enumerate(morceaux):
        markup = reply_markup if i == 0 else None
        try:
            bot.send_message(chat_id, morceau, parse_mode=parse_mode, reply_markup=markup)
        except Exception as e:
            # Fallback : on retire le parse_mode
            log_warning(
                message=f"Échec envoi avec parse_mode={parse_mode}, fallback sans Markdown",
                module="MARKDOWN",
                user_context=context,
                exception=e,
                extra={"preview": morceau[:200]},
            )
            try:
                bot.send_message(chat_id, morceau, reply_markup=markup)
            except Exception as e2:
                log_error(
                    message=f"Échec envoi même sans parse_mode",
                    module="MARKDOWN",
                    user_context=context,
                    exception=e2,
                    extra={"preview": morceau[:200]},
                )
                return False

    return True
