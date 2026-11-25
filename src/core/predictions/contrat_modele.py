# core/contrat_modele.py
"""
Contrat unique entre l'entraînement et le bot.

Le bundle stocké dans models_cache.data (colonne data, dernière ligne) est :
    base64( zlib( pickle( dict ) ) )

Le dict doit contenir exactement les clés listées dans CLES_BUNDLE.
Le bot refuse tout bundle qui ne respecte pas ce contrat : il vaut mieux
afficher « modèle indisponible » qu'un pronostic calculé avec de mauvaises features.
"""
import base64
import pickle
import zlib

VERSION_CONTRAT = 2

# Ordre exact des features passées au modèle. Ne jamais changer sans
# réentraîner le modèle et incrémenter VERSION_CONTRAT.
FEATURE_NAMES = [
    "elo_home",
    "elo_away",
    "elo_diff",
    "forme_h",
    "forme_a",
    "forme_diff",
    "marques_h",
    "encaisses_h",
    "marques_a",
    "encaisses_a",
    "repos_h",
    "repos_a",
    "repos_diff",
]

# Paramètres de calcul partagés (entraînement et prédiction)
ELO_INITIAL = 1500.0
ELO_K = 32.0
ELO_AVANTAGE_DOMICILE = 100.0
FENETRE_FORME = 5          # nombre de matchs pour la forme et les buts
REPOS_MAX_JOURS = 14       # plafond des jours de repos
MIN_MATCHS_HISTORIQUE = 5  # minimum de matchs passés par équipe

CLES_BUNDLE = {
    "schema_version",   # == VERSION_CONTRAT
    "feature_names",    # == FEATURE_NAMES
    "models",           # dict, doit contenir "1N2" (classes : 0=dom, 1=nul, 2=ext)
    "metrics",          # dict de métriques de validation
    "etat",             # dict : état des équipes à la fin des données d'entraînement
    "date_max_donnees", # str 'YYYY-MM-DD' : date du dernier match utilisé
    "date_entrainement",# str ISO
}


class ContratInvalide(Exception):
    """Le bundle ne respecte pas le contrat."""


def encoder_bundle(bundle: dict) -> str:
    """Sérialise un bundle en texte base64 prêt à être inséré dans models_cache."""
    _verifier(bundle)
    brut = pickle.dumps(bundle, protocol=4)
    return base64.b64encode(zlib.compress(brut)).decode("ascii")


def decoder_bundle(donnees) -> dict:
    """Décode et valide un bundle lu depuis models_cache.data."""
    if donnees is None or len(donnees) == 0:
        raise ContratInvalide("Bundle vide.")
    if isinstance(donnees, (bytes, bytearray)):
        try:
            donnees = donnees.decode("ascii")
        except UnicodeDecodeError:
            raise ContratInvalide("Format inattendu (binaire brut).")
    try:
        bundle = pickle.loads(zlib.decompress(base64.b64decode(donnees)))
    except Exception as e:
        raise ContratInvalide(f"Décodage impossible : {e}")
    _verifier(bundle)
    return bundle


def _verifier(bundle):
    if not isinstance(bundle, dict):
        raise ContratInvalide("Le bundle n'est pas un dictionnaire.")
    manquantes = CLES_BUNDLE - set(bundle.keys())
    if manquantes:
        raise ContratInvalide(f"Clés manquantes : {sorted(manquantes)}")
    if bundle["schema_version"] != VERSION_CONTRAT:
        raise ContratInvalide(
            f"Version {bundle['schema_version']} attendue {VERSION_CONTRAT} : réentraîne le modèle."
        )
    if list(bundle["feature_names"]) != FEATURE_NAMES:
        raise ContratInvalide("Liste de features différente du contrat : réentraîne le modèle.")
    modeles = bundle["models"]
    if not isinstance(modeles, dict) or "1N2" not in modeles:
        raise ContratInvalide("Le marché 1N2 est absent du bundle.")
    if not hasattr(modeles["1N2"], "predict_proba"):
        raise ContratInvalide("Le modèle 1N2 n'a pas de méthode predict_proba.")
    if not isinstance(bundle["etat"], dict):
        raise ContratInvalide("L'état des équipes est invalide.")
