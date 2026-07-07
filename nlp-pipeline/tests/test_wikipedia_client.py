"""Tests du client API Wikipédia avec mocks httpx (respx)."""

import pytest
import respx
from httpx import Response

from pipeline.wikipedia_client import (
    fetch_article_detail,
    fetch_pageviews,
    fetch_random_articles,
    normalize_title,
)

API_URL = "https://fr.wikipedia.org/w/api.php"


class TestNormalizeTitle:
    def test_remplace_underscores(self):
        assert normalize_title("Jean_Dupont") == "Jean Dupont"

    def test_decode_url(self):
        assert normalize_title("Jean%20Dupont") == "Jean Dupont"

    def test_decode_html(self):
        assert normalize_title("Jean &amp; Paul") == "Jean & Paul"

    def test_strip_whitespace(self):
        assert normalize_title("  Paris  ") == "Paris"

    def test_deja_normalise(self):
        assert normalize_title("Marseille") == "Marseille"


class TestFetchPageviews:
    @respx.mock
    @pytest.mark.asyncio
    async def test_retourne_total_vues(self):
        route = respx.get(API_URL).respond(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "pageviews": {
                                "2026-06-01": 100,
                                "2026-06-02": 200,
                                "2026-06-03": 150,
                            }
                        }
                    ]
                }
            },
        )
        result = await fetch_pageviews("Test")
        assert result == 450
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_pas_de_donnees(self):
        route = respx.get(API_URL).respond(
            200,
            json={"query": {"pages": [{"pageviews": None}]}},
        )
        result = await fetch_pageviews("Test")
        assert result == 0
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_page_manquante(self):
        route = respx.get(API_URL).respond(
            200,
            json={"query": {"pages": [{"missing": True}]}},
        )
        result = await fetch_pageviews("Test")
        assert result == 0
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_sur_429(self):
        respx.get(API_URL).mock(
            side_effect=[
                Response(429),
                Response(
                    200,
                    json={
                        "query": {
                            "pages": [{"pageviews": {"2026-06-01": 50}}]
                        }
                    },
                ),
            ]
        )
        result = await fetch_pageviews("Test")
        assert result == 50

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_sur_timeout(self):
        from httpx import TimeoutException

        respx.get(API_URL).mock(
            side_effect=[
                TimeoutException("timeout"),
                Response(
                    200,
                    json={
                        "query": {
                            "pages": [{"pageviews": {"2026-06-01": 30}}]
                        }
                    },
                ),
            ]
        )
        result = await fetch_pageviews("Test")
        assert result == 30


class TestFetchArticleDetail:
    @respx.mock
    @pytest.mark.asyncio
    async def test_article_trouve(self):
        route = respx.get(API_URL).respond(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "pageid": 123,
                            "title": "Paris",
                            "extract": "Paris est la capitale de la France.",
                            "categories": [
                                {"title": "Catégorie:Capitales"}
                            ],
                            "pageprops": {"wikibase_item": "Q90"},
                            "pageviews": {"2026-06-01": 500},
                        }
                    ]
                }
            },
        )
        result = await fetch_article_detail("Paris")
        assert result is not None
        assert result["titre"] == "Paris"
        assert result["pageid"] == 123
        assert result["contenu"] == "Paris est la capitale de la France."
        assert "Catégorie:Capitales" in result["categories"]
        assert result["categorie"] == "Capitales"
        assert result["popularite"] == 500
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_article_inexistant(self):
        route = respx.get(API_URL).respond(
            200,
            json={
                "query": {
                    "pages": [
                        {"missing": True, "title": "ArticleInexistant"}
                    ]
                }
            },
        )
        result = await fetch_article_detail("ArticleInexistant")
        assert result is None
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_categorie_admin_ignoree(self):
        route = respx.get(API_URL).respond(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "pageid": 456,
                            "title": "Soleil",
                            "extract": "Le Soleil est une étoile.",
                            "categories": [
                                {"title": "Catégorie:Article de qualité"},
                                {"title": "Catégorie:Astronomie"},
                            ],
                            "pageprops": {},
                            "pageviews": None,
                        }
                    ]
                }
            },
        )
        result = await fetch_article_detail("Soleil")
        assert result is not None
        assert result["categorie"] == "Astronomie"
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_apres_erreur(self):
        respx.get(API_URL).mock(
            side_effect=[
                Response(500),
                Response(
                    200,
                    json={
                        "query": {
                            "pages": [
                                {
                                    "pageid": 789,
                                    "title": "Test",
                                    "extract": "Contenu.",
                                    "categories": [],
                                    "pageprops": {},
                                    "pageviews": None,
                                }
                            ]
                        }
                    },
                ),
            ]
        )
        result = await fetch_article_detail("Test")
        assert result is not None
        assert result["titre"] == "Test"


class TestFetchRandomArticles:
    @respx.mock
    @pytest.mark.asyncio
    async def test_recupere_et_details(self):
        respx.get(API_URL).mock(
            side_effect=[
                # Premier appel : list=random
                Response(
                    200,
                    json={
                        "query": {
                            "random": [
                                {"id": 1, "title": "Paris"},
                                {"id": 2, "title": "Lyon"},
                            ]
                        }
                    },
                ),
                # Deuxième appel : détails des articles
                Response(
                    200,
                    json={
                        "query": {
                            "pages": [
                                {
                                    "pageid": 1,
                                    "title": "Paris",
                                    "extract": "Paris est une ville.",
                                    "categories": [
                                        {"title": "Catégorie:Géographie"}
                                    ],
                                    "pageprops": {},
                                    "pageviews": {"2026-06-01": 300},
                                },
                                {
                                    "pageid": 2,
                                    "title": "Lyon",
                                    "extract": "Lyon est une ville.",
                                    "categories": [
                                        {"title": "Catégorie:Géographie"}
                                    ],
                                    "pageprops": {},
                                    "pageviews": {"2026-06-01": 200},
                                },
                            ]
                        }
                    },
                ),
            ]
        )
        results = await fetch_random_articles(2)
        assert len(results) == 2
        assert results[0]["titre"] == "Paris"
        assert results[1]["titre"] == "Lyon"

    @respx.mock
    @pytest.mark.asyncio
    async def test_aucun_titre_recupere(self):
        route = respx.get(API_URL).respond(
            200,
            json={"query": {"random": []}},
        )
        results = await fetch_random_articles(5)
        assert len(results) == 0
        assert route.called
