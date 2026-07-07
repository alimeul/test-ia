"""Tests unitaires des fonctions de filtrage."""


from pipeline.filters import (
    has_sensitive_category,
    is_duplicate,
    is_eligible,
    is_long_enough,
    is_popular_enough,
    is_short_enough,
)


class TestIsLongEnough:
    def test_suffisamment_long(self):
        assert is_long_enough("x" * 2000, min_chars=2000) is True

    def test_trop_court(self):
        assert is_long_enough("x" * 1999, min_chars=2000) is False

    def test_texte_vide(self):
        assert is_long_enough("", min_chars=2000) is False


class TestIsShortEnough:
    def test_suffisamment_court(self):
        assert is_short_enough("x" * 50000, max_chars=50000) is True

    def test_trop_long(self):
        assert is_short_enough("x" * 50001, max_chars=50000) is False

    def test_texte_vide(self):
        assert is_short_enough("", max_chars=50000) is True


class TestHasSensitiveCategory:
    def test_categorie_sensible_trouvee(self):
        categories = ["Catégorie:Histoire", "Catégorie:Année de mort en France"]
        sensitive = ["Mort"]
        assert has_sensitive_category(categories, sensitive) is True

    def test_categorie_sensible_non_trouvee(self):
        categories = ["Catégorie:Histoire", "Catégorie:Géographie"]
        sensitive = ["Mort", "Violence"]
        assert has_sensitive_category(categories, sensitive) is False

    def test_categorie_vide(self):
        assert has_sensitive_category([], ["Mort"]) is False

    def test_insensible_a_la_casse(self):
        categories = ["Catégorie:VIOLENCE politique"]
        sensitive = ["violence"]
        assert has_sensitive_category(categories, sensitive) is True

    def test_correspondance_partielle(self):
        categories = ["Catégorie:Année de mort dans le sport"]
        sensitive = ["Mort"]
        assert has_sensitive_category(categories, sensitive) is True

    def test_aucune_liste_sensible(self):
        assert has_sensitive_category(["Catégorie:Histoire"]) is False

    def test_motif_au_milieu_du_nom(self):
        categories = ["Catégorie:Assassinat politique"]
        sensitive = ["Assassinat"]
        assert has_sensitive_category(categories, sensitive) is True


class TestIsPopularEnough:
    def test_populaire(self):
        assert is_popular_enough(100, min_views=50) is True

    def test_pas_assez_populaire(self):
        assert is_popular_enough(10, min_views=50) is False

    def test_exactement_le_seuil(self):
        assert is_popular_enough(50, min_views=50) is True

    def test_pageviews_none(self):
        assert is_popular_enough(None, min_views=50) is True


class TestIsDuplicate:
    def test_titre_deja_present(self):
        existing = {"Paris", "Lyon"}
        assert is_duplicate(existing, "Paris") is True

    def test_titre_nouveau(self):
        existing = {"Paris", "Lyon"}
        assert is_duplicate(existing, "Marseille") is False

    def test_insensible_a_la_casse(self):
        existing = {"paris"}
        assert is_duplicate(existing, "Paris") is True

    def test_ensemble_vide(self):
        assert is_duplicate(set(), "Paris") is False


class TestIsEligible:
    def test_article_valide(self):
        article = {
            "titre": "Astronomie",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Sciences"],
            "popularite": 500,
        }
        assert is_eligible(article) is True

    def test_trop_court(self):
        article = {
            "titre": "Court",
            "contenu": "x" * 100,
            "categories": ["Catégorie:Sciences"],
            "popularite": 500,
        }
        assert is_eligible(article) is False

    def test_trop_long(self):
        article = {
            "titre": "Long",
            "contenu": "x" * 60000,
            "categories": ["Catégorie:Sciences"],
            "popularite": 500,
        }
        assert is_eligible(article) is False

    def test_categorie_sensible(self):
        article = {
            "titre": "Guerre",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Guerre mondiale"],
            "popularite": 500,
        }
        assert is_eligible(article) is False

    def test_popularite_insuffisante(self):
        article = {
            "titre": "Obscur",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Sciences"],
            "popularite": 10,
        }
        assert is_eligible(article, min_views=50) is False

    def test_titre_existant(self):
        article = {
            "titre": "Paris",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Géographie"],
            "popularite": 500,
        }
        assert is_eligible(article, existing_titles={"Paris"}) is False

    def test_titre_existant_case_insensitive(self):
        article = {
            "titre": "paris",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Géographie"],
            "popularite": 500,
        }
        assert is_eligible(article, existing_titles={"Paris"}) is False

    def test_popularite_none_considere_eligible(self):
        article = {
            "titre": "ArticleSansVues",
            "contenu": "x" * 2000,
            "categories": ["Catégorie:Sciences"],
            "popularite": None,
        }
        assert is_eligible(article, min_views=50) is True

    def test_categories_vides(self):
        article = {
            "titre": "SansCat",
            "contenu": "x" * 2000,
            "categories": [],
            "popularite": 500,
        }
        assert is_eligible(article) is True

    def test_parametres_personnalises(self):
        article = {
            "titre": "Test",
            "contenu": "x" * 500,
            "categories": [],
            "popularite": 5,
        }
        assert (
            is_eligible(
                article,
                min_chars=100,
                max_chars=1000,
                min_views=1,
            )
            is True
        )

    def test_article_sans_contenu(self):
        article = {
            "titre": "Vide",
            "contenu": "",
            "categories": [],
            "popularite": 500,
        }
        assert is_eligible(article) is False

    def test_article_sans_cle(self):
        assert is_eligible({}) is False
