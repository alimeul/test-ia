from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///../nlp-pipeline/data/wikidle.db"
    REDACTED_ARTICLES_DIR: str = "../nlp-pipeline/data/defis"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def database_url_abs(self) -> str:
        backend_dir = Path(__file__).resolve().parent.parent
        db_rel = self.DATABASE_URL.replace("sqlite:///", "")
        db_abs = (backend_dir / db_rel).resolve()
        db_abs.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_abs}"


settings = Settings()
