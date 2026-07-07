from datetime import date

from pydantic import BaseModel


class DefiLancement(BaseModel):
    date: date
    texte_caviarde: str
    nb_indices_disponibles: int
    difficulte: dict


class DefiResume(BaseModel):
    date: str
    difficulte: float


class ProposerTitreRequest(BaseModel):
    titre_propose: str


class ProposerTitreResponse(BaseModel):
    correct: bool
    essais_restants: int
    gagne: bool
    titre: str | None = None


class RevelerIndiceRequest(BaseModel):
    pass


class RevelerIndiceResponse(BaseModel):
    indice: str
    indice_index: int
    indices_restants: int


class PartieEtat(BaseModel):
    essais_effectues: int
    essais_restants: int
    indices_reveles: int
    indices_restants: int
    gagne: bool
    termine: bool
    score: int
