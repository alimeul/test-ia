"""Configuration du pipeline NLP via Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "WIKIDLE_"}

    WIKIPEDIA_API_URL: str = "https://fr.wikipedia.org/w/api.php"
    WIKIPEDIA_LANG: str = "fr"
    DB_PATH: str = "data/wikidle.db"
    ARTICLE_MIN_CHARS: int = 2000
    ARTICLE_MAX_CHARS: int = 50000
    POPULARITE_MIN: int = 50
    FETCH_COUNT: int = 50

    SENSITIVE_CATEGORIES: list[str] = [
        "Mort",
        "Décès",
        "Suicide",
        "Meurtre",
        "Homicide",
        "Crime",
        "Violence",
        "Guerre",
        "Conflit",
        "Terrorisme",
        "Génocide",
        "Torture",
        "Viol",
        "Pornographie",
        "Sexualité",
        "Drogue",
        "Maladie",
        "Pandémie",
        "Catastrophe",
        "Accident",
        "Arme",
        "Explosion",
        "Incendie",
        "Disparition",
        "Enlèvement",
        "Assassinat",
        "Nazisme",
        "Famine",
        "Pédophilie",
        "Inceste",
    ]


settings = Settings()
