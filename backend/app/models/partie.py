from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Partie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    defi_id: int = Field(foreign_key="defi.id", index=True)
    session_id: str = Field(index=True)
    essais_effectues: int = Field(default=0)
    indices_reveles: int = Field(default=0)
    max_essais: int = Field(default=5)
    max_indices: int = Field(default=10)
    gagne: bool = Field(default=False)
    termine: bool = Field(default=False)
    score: int = Field(default=0)
    mots_reveles: str = Field(default="[]")  # JSON list of words revealed by guessing
    mots_proposes: str = Field(default="[]")  # JSON list of all proposed words [{mot, trouve}]
    date_partie: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
