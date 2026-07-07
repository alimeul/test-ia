
from pydantic import BaseModel


class PartieHistorique(BaseModel):
    date: str
    gagne: bool
    score: int
    essais: int
    indices: int
