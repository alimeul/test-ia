"""Client HTTP asynchrone pour l'API Wikipédia.

Utilise httpx avec gestion d'erreurs (timeout, 429) et tentative de retry.
"""

import html
from urllib.parse import unquote

import httpx

from pipeline.config import settings

API_URL = settings.WIKIPEDIA_API_URL

ADMIN_CATEGORY_PREFIXES = (
    "Catégorie:Article",
    "Catégorie:Page",
    "Catégorie:Projet",
    "Catégorie:Portail",
    "Catégorie:Wikipédia",
    "Catégorie:Redirection",
    "Catégorie:Maintenance",
)


def normalize_title(title: str) -> str:
    """Nettoie un titre Wikipédia : remplace _ par espaces, decode URL et entités HTML."""
    title = title.replace("_", " ")
    title = unquote(title)
    title = html.unescape(title)
    return title.strip()


async def fetch_pageviews(title: str) -> int:
    """Récupère le nombre total de vues des 60 derniers jours pour un article."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "pageviews",
        "titles": title,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(2):
            try:
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                pages = data.get("query", {}).get("pages", [])
                if pages:
                    pageviews_data = pages[0].get("pageviews")
                    if pageviews_data:
                        return sum(v for v in pageviews_data.values() if v is not None)
                return 0
            except (httpx.TimeoutException, httpx.HTTPStatusError):
                if attempt == 0:
                    continue
                raise
    return 0


async def fetch_article_detail(title: str) -> dict | None:
    """Récupère le contenu complet, les catégories et métadonnées d'un article.

    Retourne un dict avec les clés :
        pageid, titre, contenu, categories, categorie, popularite
    ou None si l'article n'existe pas.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await _fetch_articles_detail(client, [title])
        return results[0] if results else None


async def fetch_random_articles(count: int = 10) -> list[dict]:
    """Récupère des articles aléatoires avec leurs détails complets.

    Utilise list=random pour obtenir des titres aléatoires,
    puis récupère les détails par lots de 50.
    """
    titles = await _fetch_random_titles(count)
    if not titles:
        return []

    articles: list[dict] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i in range(0, len(titles), 50):
            batch = titles[i : i + 50]
            batch_articles = await _fetch_articles_detail(client, batch)
            articles.extend(batch_articles)
    return articles


async def _fetch_random_titles(count: int) -> list[str]:
    """Récupère des titres aléatoires depuis l'API Wikipédia."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": min(count, 500),
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(2):
            try:
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                titles = [
                    normalize_title(item["title"])
                    for item in data.get("query", {}).get("random", [])
                ]
                return titles[:count]
            except (httpx.TimeoutException, httpx.HTTPStatusError):
                if attempt == 0:
                    continue
                raise
    return []


async def _fetch_articles_detail(
    client: httpx.AsyncClient,
    titles: list[str],
) -> list[dict]:
    """Récupère les détails d'une liste de titres en un seul appel API.

    Inclut le contenu texte, les catégories, les pageprops et les pageviews.
    """
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "extracts|categories|pageprops|pageviews",
        "explaintext": 1,
        "exchars": 60000,
        "cllimit": "max",
        "titles": "|".join(titles),
    }
    for attempt in range(2):
        try:
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            articles: list[dict] = []
            for page in data.get("query", {}).get("pages", []):
                if "missing" in page:
                    continue

                titre = normalize_title(page.get("title", ""))
                categories_raw = [
                    c["title"] for c in page.get("categories", [])
                ]

                main_category = "Général"
                for cat_full in categories_raw:
                    if not cat_full.startswith(ADMIN_CATEGORY_PREFIXES):
                        main_category = cat_full.replace("Catégorie:", "", 1)
                        break

                pageviews_data = page.get("pageviews")
                popularite = 0
                if pageviews_data:
                    popularite = sum(
                        v for v in pageviews_data.values() if v is not None
                    )

                article = {
                    "pageid": page.get("pageid"),
                    "titre": titre,
                    "contenu": page.get("extract", ""),
                    "categories": categories_raw,
                    "categorie": main_category,
                    "popularite": popularite,
                }
                articles.append(article)
            return articles
        except (httpx.TimeoutException, httpx.HTTPStatusError):
            if attempt == 0:
                continue
            raise
    return []
