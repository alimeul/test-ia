"""Tests du module de calcul de difficulté."""

from pipeline.difficulte import calculer_score_difficulte


class TestScoreDifficulte:
    def test_article_populaire_facile(self):
        resultat = calculer_score_difficulte(
            popularite=1000,
            total_tokens=200,
            tokens_masques=50,
            entites_masquees=2,
            longueur_texte=1500,
            nb_indices=10,
        )
        assert resultat["score"] < 5.0
        assert resultat["niveau"] in ("facile", "moyen")

    def test_article_peu_connu_difficile(self):
        resultat = calculer_score_difficulte(
            popularite=0,
            total_tokens=200,
            tokens_masques=180,
            entites_masquees=8,
            longueur_texte=1500,
            nb_indices=2,
        )
        assert resultat["score"] > 5.0
        assert resultat["niveau"] in ("difficile", "expert")

    def test_contient_sous_scores(self):
        resultat = calculer_score_difficulte(
            popularite=500,
            total_tokens=100,
            tokens_masques=30,
            entites_masquees=3,
            longueur_texte=1000,
            nb_indices=5,
        )
        assert "popularite" in resultat["sous_scores"]
        assert "ratio_visible" in resultat["sous_scores"]
        assert "indices_disponibles" in resultat["sous_scores"]
        assert "entites" in resultat["sous_scores"]

    def test_score_dans_intervalle(self):
        for pop in [0, 10, 100, 500, 1000, 5000]:
            resultat = calculer_score_difficulte(
                popularite=pop,
                total_tokens=100,
                tokens_masques=50,
                entites_masquees=3,
                longueur_texte=1000,
                nb_indices=5,
            )
            assert 0.0 <= resultat["score"] <= 10.0

    def test_tous_tokens_masques(self):
        resultat = calculer_score_difficulte(
            popularite=0,
            total_tokens=100,
            tokens_masques=100,
            entites_masquees=10,
            longueur_texte=1000,
            nb_indices=0,
        )
        assert resultat["score"] >= 6.0
        assert resultat["niveau"] in ("difficile", "expert")

    def test_aucun_token_masque(self):
        resultat = calculer_score_difficulte(
            popularite=1000,
            total_tokens=100,
            tokens_masques=0,
            entites_masquees=0,
            longueur_texte=1000,
            nb_indices=20,
        )
        assert resultat["score"] <= 3.0
        assert resultat["niveau"] == "facile"
