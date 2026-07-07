import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas.defi import (
    DefiLancement,
    PartieEtat,
    ProposerTitreRequest,
    ProposerTitreResponse,
    RevelerIndiceRequest,
    RevelerIndiceResponse,
)
from app.services.defi_service import (
    check_answer,
    get_defi_by_date,
    get_partie_etat,
    reveler_indice,
)

router = APIRouter(prefix="/defis", tags=["defis"])


@router.get("/aujourdhui", response_model=DefiLancement)
async def defi_du_jour(session: Session = Depends(get_session)):
    defi = get_defi_by_date(session)
    if defi is None:
        raise HTTPException(status_code=404, detail="Aucun défi pour aujourd'hui")
    data = json.loads(defi.texte_caviarde)
    indices = json.loads(defi.indices)
    return DefiLancement(
        date=defi.date_publication,
        texte_caviarde=data["texte"],
        nb_indices_disponibles=min(len(indices), 10),
        difficulte={"score": defi.score_difficulte},
    )


@router.get("/aujourdhui/partie", response_model=PartieEtat)
async def etat_partie(session_id: str = Query(...), session: Session = Depends(get_session)):
    defi = get_defi_by_date(session)
    if defi is None:
        raise HTTPException(status_code=404, detail="Aucun défi pour aujourd'hui")
    return PartieEtat(**get_partie_etat(session, defi, session_id))


@router.post("/aujourdhui/proposer", response_model=ProposerTitreResponse)
async def proposer_titre(
    body: ProposerTitreRequest,
    session_id: str = Query(...),
    session: Session = Depends(get_session),
):
    defi = get_defi_by_date(session)
    if defi is None:
        raise HTTPException(status_code=404, detail="Aucun défi pour aujourd'hui")

    resultat = check_answer(session, defi, session_id, body.titre_propose)

    if "erreur" in resultat:
        raise HTTPException(status_code=400, detail=resultat["erreur"])

    return ProposerTitreResponse(
        correct=resultat["correct"],
        essais_restants=resultat["essais_restants"],
        gagne=resultat["gagne"],
        titre=resultat.get("titre"),
    )


@router.post("/aujourdhui/reveler", response_model=RevelerIndiceResponse)
async def reveler_indice_endpoint(
    body: RevelerIndiceRequest,
    session_id: str = Query(...),
    session: Session = Depends(get_session),
):
    defi = get_defi_by_date(session)
    if defi is None:
        raise HTTPException(status_code=404, detail="Aucun défi pour aujourd'hui")

    resultat = reveler_indice(session, defi, session_id)

    if "erreur" in resultat:
        raise HTTPException(status_code=400, detail=resultat["erreur"])

    return RevelerIndiceResponse(**resultat)
