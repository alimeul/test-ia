from pydantic import BaseModel


class PartieHistorique(BaseModel):
    date: str
    gagne: bool
    score: int
    essais: int
    indices: int


class StatsSession(BaseModel):
    total_parties: int
    total_gagnees: int
    taux_reussite: float
    serie_actuelle: int
    meilleure_serie: int
    meilleur_score: int
