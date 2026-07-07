from datetime import date

from sqlalchemy import Text
from sqlmodel import Field, SQLModel


class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titre: str = Field(index=True)
    contenu_original: str = Field(sa_type=Text)
    categorie: str = Field(index=True)
    popularite: int = Field(default=0)
    date_import: date
