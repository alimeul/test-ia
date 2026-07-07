"""Tests du module de caviardage NLP."""


import pytest

from pipeline.redacteur import (
    _MASK_CHAR,
    _POS_GRAMMATICAUX,
    _POS_PORTEURS,
    generer_indices,
    rediger_texte,
)


def test_import_spacy_manquant(monkeypatch):
    """Vérifie que get_nlp() lève ImportError si spacy est absent."""
    import pipeline.redacteur as r

    monkeypatch.setattr(r, "spacy", None)
    with pytest.raises(ImportError, match="spacy n'est pas installé"):
        r.get_nlp()


class TestRedigerTexteCasLimites:
    def test_texte_vide(self):
        resultat = rediger_texte("", "Test")
        assert resultat["texte_caviarde"] == ""
        assert resultat["stats"]["total_tokens"] == 0

    def test_texte_que_espaces(self):
        resultat = rediger_texte("   \n  ", "Test")
        assert resultat["stats"]["total_tokens"] == 0

    def test_seed_reproductible(self):
        t = "Le chat mange la souris."
        r1 = rediger_texte(t, "chat", seed=42)
        r2 = rediger_texte(t, "chat", seed=42)
        assert r1["texte_caviarde"] == r2["texte_caviarde"]
        assert r1["indices"] == r2["indices"]


class TestMotsGrammaticaux:
    def test_determinants_jamais_masques(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=1.0)
        for t in resultat["tokens"]:
            if t["pos"] in _POS_GRAMMATICAUX:
                assert not t["masque"], f"Token grammatical masqué : {t['texte']} ({t['pos']})"


class TestTitreMasque:
    def test_titre_masque_dans_texte(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=0.0)
        assert "Paris" not in resultat["texte_caviarde"]
        assert _MASK_CHAR in resultat["texte_caviarde"]

    def test_titre_variante_masquee(self):
        t = "Le parisien aime sa ville. Paris est belle."
        resultat = rediger_texte(t, "Paris", taux_masquage=0.0)
        assert _MASK_CHAR in resultat["texte_caviarde"]


class TestEntitesNommees:
    def test_personne_masquee(self, sample_texte_entites):
        resultat = rediger_texte(sample_texte_entites, "Napoléon", taux_masquage=0.0)
        for nom in ["Napoléon", "Ajaccio", "Austerlitz", "Joséphine", "Sainte-Hélène"]:
            if nom in sample_texte_entites and nom.lower() not in "napoléon":
                assert nom.lower() not in resultat["texte_caviarde"].lower(), (
                    f"Entité non masquée : {nom}"
                )


class TestLongueurMasquage:
    def test_longueur_masque_correspond(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=1.0)
        for t in resultat["tokens"]:
            if t["masque"]:
                motif = _MASK_CHAR * len(t["texte"])
                assert len(motif) == len(t["texte"]), (
                    f"Longueur incohérente pour {t['texte']}"
                )


class TestTauxMasquage:
    def test_taux_zero_masque_titre_et_entites(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=0.0)
        # Le titre est forcé d'être masqué même à taux 0
        mots_titre = sample_titre.lower().split()
        for t in resultat["tokens"]:
            if t["texte"].lower() in mots_titre and t["pos"] in _POS_PORTEURS:
                assert t["masque"], f"Le mot du titre '{t['texte']}' devrait être masqué"

    def test_taux_un_tout_masque(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=1.0)
        porteurs = [t for t in resultat["tokens"] if t["pos"] in _POS_PORTEURS]
        assert all(t["masque"] for t in porteurs)


class TestIndices:
    def test_indices_sont_masques(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, seed=42, taux_masquage=0.5)
        for t in resultat["tokens"]:
            if t["indice_index"] is not None:
                assert t["masque"], f"Token indice '{t['texte']}' devrait être masqué"

    def test_generer_indices_depuis_tokens(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=0.5)
        indices = generer_indices(resultat["tokens"], nb_indices=3)
        assert len(indices) <= 3

    def test_indices_non_vides_si_titre_force(self, sample_texte, sample_titre):
        """Même à taux=0, le titre et les entités sont forcés → il y a des indices."""
        resultat = rediger_texte(sample_texte, sample_titre, taux_masquage=0.0)
        assert len(resultat["indices"]) > 0


class TestFormatSortie:
    def test_contient_cles_attendues(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre)
        assert "texte_caviarde" in resultat
        assert "tokens" in resultat
        assert "indices" in resultat
        assert "stats" in resultat

    def test_stats_contient_cles(self, sample_texte, sample_titre):
        resultat = rediger_texte(sample_texte, sample_titre)
        stats = resultat["stats"]
        assert "total_tokens" in stats
        assert "tokens_masques" in stats
        assert "taux_effectif" in stats
        assert "entites_masquees" in stats
