"""Score de difficulté pour les articles caviardés."""

_NIVEAUX = [
    ("facile", 0.0, 3.5),
    ("moyen", 3.5, 6.0),
    ("difficile", 6.0, 8.5),
    ("expert", 8.5, 10.1),
]


def _mapping_lineaire(valeur: float, max_ref: float, sens: str = "direct") -> float:
    """Mappe une valeur sur une échelle 0-10.

    sens="direct" : plus la valeur est haute, plus le score est haut.
    sens="inverse" : plus la valeur est haute, plus le score est bas.
    """
    if max_ref <= 0:
        return 5.0
    score = (min(valeur, max_ref) / max_ref) * 10.0
    if sens == "inverse":
        score = 10.0 - score
    return max(0.0, min(10.0, score))


def _determiner_niveau(score: float) -> str:
    for niveau, seuil_bas, seuil_haut in _NIVEAUX:
        if seuil_bas <= score < seuil_haut:
            return niveau
    return "expert"


def calculer_score_difficulte(
    popularite: int = 0,
    total_tokens: int = 0,
    tokens_masques: int = 0,
    entites_masquees: int = 0,
    longueur_texte: int = 0,
    nb_indices: int = 5,
) -> dict:
    """Calcule un score de difficulté pour un article caviardé (0 = facile, 10 = difficile).

    Pondération :
      - popularité (30%) : populaire → facile (inverse)
      - ratio visible (30%) : peu visible → difficile (inverse)
      - indices disponibles (20%) : peu d'indices → difficile (inverse)
      - entités spécifiques (20%) : beaucoup d'entités → difficile (direct)
    """
    score_pop = _mapping_lineaire(float(popularite), 1000.0, sens="inverse")
    if popularite == 0:
        score_pop = 7.0

    ratio_visible = 1.0
    if total_tokens > 0:
        ratio_visible = (total_tokens - tokens_masques) / total_tokens
    score_visible = _mapping_lineaire(ratio_visible, 1.0, sens="inverse")

    score_indices = _mapping_lineaire(float(nb_indices), 15.0, sens="inverse")

    score_entites = _mapping_lineaire(float(entites_masquees), 8.0, sens="direct")

    score_global = (
        score_pop * 0.30
        + score_visible * 0.30
        + score_indices * 0.20
        + score_entites * 0.20
    )

    return {
        "score": round(score_global, 2),
        "sous_scores": {
            "popularite": round(score_pop, 2),
            "ratio_visible": round(score_visible, 2),
            "indices_disponibles": round(score_indices, 2),
            "entites": round(score_entites, 2),
        },
        "niveau": _determiner_niveau(score_global),
    }
