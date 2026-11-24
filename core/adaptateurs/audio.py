# core/adaptateurs/audio.py
"""
Adaptateur de synthèse vocale / génération audio.

Utilisé pour : résumé vocal (30s), commentaire live audio, messages audio.
Configuration : clés selon le fournisseur (Google TTS, ElevenLabs, etc.).
"""

from __future__ import annotations

import os
from typing import Any

from core.adaptateurs.base import FournisseurAudio, ResultatAdaptateur, _resultat


class AdaptateurAudio(FournisseurAudio):
    """Adaptateur audio générique.

    Le fournisseur par défaut est un adaptateur "neutre" qui retourne une
    erreur "non configuré" tant qu'aucune clé TTS n'est fournie.
    """

    def __init__(self):
        self._cle_tts = os.environ.get("TTS_API_KEY", "")
        self._fournisseur = os.environ.get("TTS_FOURNISSEUR", "google")  # google, elevenlabs, azure

    def generer_audio(self, texte: str, langue: str = "fr") -> ResultatAdaptateur:
        """Génère un fichier audio à partir d'un texte.

        Retourne (succes, chemin_fichier_audio, erreur).
        Si aucun fournisseur n'est configuré, retourne succes=False.
        """
        if not self._cle_tts:
            return _resultat(False, None, "Aucune clé TTS configurée (TTS_API_KEY)")
        try:
            if self._fournisseur == "google":
                return self._generer_google_tts(texte, langue)
            if self._fournisseur == "elevenlabs":
                return self._generer_elevenlabs(texte, langue)
            return _resultat(False, None, f"Fournisseur TTS inconnu : {self._fournisseur}")
        except Exception as e:  # pragma: no cover - dépend du fournisseur externe
            return _resultat(False, None, f"Erreur génération audio : {type(e).__name__}")

    def _generer_google_tts(self, texte: str, langue: str) -> ResultatAdaptateur:
        # Placeholder : implémentation réelle avec google-cloud-texttospeech
        return _resultat(False, None, "Google TTS non encore implémenté (clé configurée mais SDK absent)")

    def _generer_elevenlabs(self, texte: str, langue: str) -> ResultatAdaptateur:
        # Placeholder : implémentation réelle avec l'API ElevenLabs
        return _resultat(False, None, "ElevenLabs non encore implémenté (clé configurée mais SDK absent)")
