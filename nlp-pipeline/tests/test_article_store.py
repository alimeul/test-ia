"""Tests du stockage des articles avec base SQLite temporaire."""

from datetime import date
from pathlib import Path

import pytest

from pipeline.article_store import (
    Article,
    article_exists,
    get_all_titles,
    get_statistics,
    init_db,
    save_article,
)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test_wikidle.db")


class TestInitDB:
    def test_cree_fichier_et_table(self, db_path):
        init_db(db_path)
        assert Path(db_path).exists()
        assert Article.metadata.tables["article"] is not None

    def test_idempotent(self, db_path):
        init_db(db_path)
        init_db(db_path)
        assert Path(db_path).exists()


class TestSaveArticle:
    def test_sauvegarde_et_attribue_id(self, db_path):
        init_db(db_path)
        article_data = {
            "titre": "Paris",
            "contenu": "Paris est la capitale de la France.",
            "categorie": "Géographie",
            "popularite": 500,
            "date_import": date(2026, 7, 1),
        }
        article = save_article(db_path, article_data)
        assert article.id is not None
        assert article.titre == "Paris"
        assert article.contenu_original == "Paris est la capitale de la France."
        assert article.categorie == "Géographie"
        assert article.popularite == 500
        assert article.date_import == date(2026, 7, 1)


class TestArticleExists:
    def test_existe(self, db_path):
        init_db(db_path)
        save_article(
            db_path,
            {
                "titre": "Lyon",
                "contenu": "Lyon est une ville.",
                "categorie": "Géographie",
                "popularite": 300,
            },
        )
        assert article_exists(db_path, "Lyon") is True

    def test_n_existe_pas(self, db_path):
        init_db(db_path)
        assert article_exists(db_path, "Marseille") is False

    def test_base_vide(self, db_path):
        init_db(db_path)
        assert article_exists(db_path, "Rien") is False


class TestGetAllTitles:
    def test_retourne_tous_les_titres(self, db_path):
        init_db(db_path)
        save_article(
            db_path,
            {
                "titre": "A",
                "contenu": "Article A.",
                "categorie": "Cat1",
                "popularite": 10,
            },
        )
        save_article(
            db_path,
            {
                "titre": "B",
                "contenu": "Article B.",
                "categorie": "Cat2",
                "popularite": 20,
            },
        )
        titles = get_all_titles(db_path)
        assert titles == {"A", "B"}

    def test_base_vide(self, db_path):
        init_db(db_path)
        assert get_all_titles(db_path) == set()


class TestGetStatistics:
    def test_statistiques_correctes(self, db_path):
        init_db(db_path)
        save_article(
            db_path,
            {
                "titre": "Paris",
                "contenu": "Paris.",
                "categorie": "Géographie",
                "popularite": 500,
            },
        )
        save_article(
            db_path,
            {
                "titre": "Python",
                "contenu": "Python.",
                "categorie": "Informatique",
                "popularite": 1000,
            },
        )
        save_article(
            db_path,
            {
                "titre": "Lyon",
                "contenu": "Lyon.",
                "categorie": "Géographie",
                "popularite": 300,
            },
        )
        stats = get_statistics(db_path)
        assert stats["total_articles"] == 3
        assert stats["categories"]["Géographie"] == 2
        assert stats["categories"]["Informatique"] == 1

    def test_base_vide(self, db_path):
        init_db(db_path)
        stats = get_statistics(db_path)
        assert stats["total_articles"] == 0
        assert stats["categories"] == {}
