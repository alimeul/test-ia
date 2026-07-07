from datetime import date

from pydantic import BaseModel


class DefiResponse(BaseModel):
    date: date
    texte_caviarde: str
    titre_devine: bool = False
