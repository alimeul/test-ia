"""Fixtures de test pour le pipeline NLP."""

import pytest

SAMPLE_TITRE = "Paris"

SAMPLE_TEXTE = (
    "Paris est la capitale de la France. Elle est située dans le nord du pays, "
    "sur les rives de la Seine. La ville lumière compte plus de deux millions "
    "d'habitants. Paris est célèbre pour ses monuments comme la tour Eiffel et "
    "le musée du Louvre. La ville a accueilli les Jeux Olympiques en 1900 et en 1924. "
    "Le maire actuel de Paris est Anne Hidalgo. "
    "La France est un pays d'Europe occidentale."
)

SAMPLE_TEXTE_ENTITES = (
    "Napoléon Bonaparte est né à Ajaccio en Corse. "
    "Il a été empereur des Français de 1804 à 1814. "
    "Il a remporté la bataille d'Austerlitz en 1805. "
    "Son épouse Joséphine de Beauharnais était une femme influente. "
    "Napoléon est mort le 5 mai 1821 sur l'île de Sainte-Hélène."
)


@pytest.fixture
def sample_titre() -> str:
    return SAMPLE_TITRE


@pytest.fixture
def sample_texte() -> str:
    return SAMPLE_TEXTE


@pytest.fixture
def sample_texte_entites() -> str:
    return SAMPLE_TEXTE_ENTITES


@pytest.fixture
def sample_texte_court() -> str:
    return "Ceci est un texte très court."


@pytest.fixture
def sample_texte_vide() -> str:
    return ""
