"""Schémas Pydantic partagés entre le pipeline NLP et le backend FastAPI."""

from pydantic import BaseModel


class TokenInfo(BaseModel):
    texte: str
    masque: bool
    pos: str
    indice_index: int | None = None


class StatsCaviardage(BaseModel):
    total_tokens: int
    tokens_masques: int
    taux_effectif: float
    entites_masquees: int


class ScoreDifficulte(BaseModel):
    score: float
    sous_scores: dict[str, float]
    niveau: str


class ArticleCaviarde(BaseModel):
    article_id: int
    titre: str
    texte_caviarde: str
    tokens: list[TokenInfo]
    indices: list[str]
    stats: StatsCaviardage
    difficulte: ScoreDifficulte
