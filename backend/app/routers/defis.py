import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas.defi import (
    DefiLancement,
    DefiResume,
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
from app.services.stats_service import get_defi_by_date_str, get_historique_defis

router = APIRouter(prefix="/defis", tags=["defis"])


def _build_defi_lancement(defi) -> DefiLancement:
    data = json.loads(defi.texte_caviarde)
    indices = json.loads(defi.indices)
    return DefiLancement(
        date=defi.date_publication,
        texte_caviarde=data["texte"],
        nb_indices_disponibles=min(len(indices), 10),
        difficulte={"score": defi.score_difficulte},
    )


def _get_defi_or_404(session: Session, date_str: str | None = None):
    if date_str:
        defi = get_defi_by_date_str(session, date_str)
    else:
        defi = get_defi_by_date(session)
    if defi is None:
        raise HTTPException(status_code=404, detail="Aucun défi pour cette date")
    return defi


@router.get("/aujourdhui", response_model=DefiLancement)
async def defi_du_jour(session: Session = Depends(get_session)):
    return _build_defi_lancement(_get_defi_or_404(session))


@router.get("/historique", response_model=list[DefiResume])
async def historique_defis(session: Session = Depends(get_session)):
    return get_historique_defis(session)


@router.get("/{date}", response_model=DefiLancement)
async def defi_par_date(date: str, session: Session = Depends(get_session)):
    return _build_defi_lancement(_get_defi_or_404(session, date))


@router.get("/aujourdhui/partie", response_model=PartieEtat)
async def etat_partie(session_id: str = Query(...), session: Session = Depends(get_session)):
    defi = _get_defi_or_404(session)
    return PartieEtat(**get_partie_etat(session, defi, session_id))


@router.get("/{date}/partie", response_model=PartieEtat)
async def etat_partie_date(
    date: str, session_id: str = Query(...), session: Session = Depends(get_session)
):
    defi = _get_defi_or_404(session, date)
    return PartieEtat(**get_partie_etat(session, defi, session_id))


@router.post("/aujourdhui/proposer", response_model=ProposerTitreResponse)
async def proposer_titre(
    body: ProposerTitreRequest,
    session_id: str = Query(...),
    session: Session = Depends(get_session),
):
    defi = _get_defi_or_404(session)
    resultat = check_answer(session, defi, session_id, body.titre_propose)
    if "erreur" in resultat:
        raise HTTPException(status_code=400, detail=resultat["erreur"])
    return ProposerTitreResponse(
        correct=resultat["correct"],
        essais_restants=resultat["essais_restants"],
        gagne=resultat["gagne"],
        titre=resultat.get("titre"),
    )


@router.post("/{date}/proposer", response_model=ProposerTitreResponse)
async def proposer_titre_date(
    date: str,
    body: ProposerTitreRequest,
    session_id: str = Query(...),
    session: Session = Depends(get_session),
):
    defi = _get_defi_or_404(session, date)
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
    defi = _get_defi_or_404(session)
    resultat = reveler_indice(session, defi, session_id)
    if "erreur" in resultat:
        raise HTTPException(status_code=400, detail=resultat["erreur"])
    return RevelerIndiceResponse(**resultat)


@router.post("/{date}/reveler", response_model=RevelerIndiceResponse)
async def reveler_indice_date(
    date: str,
    body: RevelerIndiceRequest,
    session_id: str = Query(...),
    session: Session = Depends(get_session),
):
    defi = _get_defi_or_404(session, date)
    resultat = reveler_indice(session, defi, session_id)
    if "erreur" in resultat:
        raise HTTPException(status_code=400, detail=resultat["erreur"])
    return RevelerIndiceResponse(**resultat)
