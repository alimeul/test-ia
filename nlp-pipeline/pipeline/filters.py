"""Fonctions de filtrage pures pour la sélection des articles Wikipédia."""

from pipeline.config import settings


def is_long_enough(text: str, min_chars: int = settings.ARTICLE_MIN_CHARS) -> bool:
    """Vérifie que le texte d'un article est suffisamment long."""
    return len(text) >= min_chars


def is_short_enough(text: str, max_chars: int = settings.ARTICLE_MAX_CHARS) -> bool:
    """Vérifie que le texte d'un article ne dépasse pas la taille maximale."""
    return len(text) <= max_chars


def has_sensitive_category(
    categories: list[str],
    sensitive_list: list[str] | None = None,
) -> bool:
    """Retourne True si au moins une catégorie correspond à un motif sensible.

    La correspondance est insensible à la casse et partielle
    (ex: "Mort" matche "Catégorie:Année de mort dans le sport").
    """
    if sensitive_list is None:
        sensitive_list = settings.SENSITIVE_CATEGORIES

    for cat in categories:
        cat_lower = cat.lower()
        for sensitive in sensitive_list:
            if sensitive.lower() in cat_lower:
                return True
    return False


def is_popular_enough(
    pageviews: int | None,
    min_views: int = settings.POPULARITE_MIN,
) -> bool:
    """Vérifie que l'article a suffisamment de vues.

    Si pageviews est None (données indisponibles), l'article est considéré éligible.
    """
    if pageviews is None:
        return True
    return pageviews >= min_views


def is_duplicate(titles: set[str], new_title: str) -> bool:
    """Vérifie si le titre a déjà été traité (comparaison insensible à la casse)."""
    return new_title.lower() in {t.lower() for t in titles}


def is_eligible(
    article: dict,
    existing_titles: set[str] | None = None,
    min_chars: int = settings.ARTICLE_MIN_CHARS,
    max_chars: int = settings.ARTICLE_MAX_CHARS,
    min_views: int = settings.POPULARITE_MIN,
    sensitive_list: list[str] | None = None,
) -> bool:
    """Combine tous les filtres pour déterminer si un article est éligible.

    Retourne True si l'article passe tous les critères.
    """
    if existing_titles is None:
        existing_titles = set()

    titre = article.get("titre", "")
    if is_duplicate(existing_titles, titre):
        return False

    texte = article.get("contenu", "")
    if not is_long_enough(texte, min_chars):
        return False
    if not is_short_enough(texte, max_chars):
        return False

    categories = article.get("categories", [])
    if has_sensitive_category(categories, sensitive_list):
        return False

    pageviews = article.get("popularite")
    if not is_popular_enough(pageviews, min_views):
        return False

    return True
