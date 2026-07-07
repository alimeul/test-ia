from datetime import date

from sqlalchemy import Text
from sqlmodel import Field, SQLModel


class Defi(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    date_publication: date = Field(index=True, unique=True)
    texte_caviarde: str = Field(sa_type=Text)
    score_difficulte: float = Field(default=0.0)
    indices: str = Field(sa_type=Text, default="[]")
