import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
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
    get_ou_creer_partie,
    get_partie_etat,
    reconstruire_texte,
    reveler_indice,
)
from app.services.stats_service import get_defi_by_date_str, get_historique_defis

router = APIRouter(prefix="/defis", tags=["defis"])
limiter = Limiter(key_func=get_remote_address)


def _build_defi_lancement(defi, session: Session | None = None, session_id: str | None = None) -> DefiLancement:
    data = json.loads(defi.texte_caviarde)
    indices = json.loads(defi.indices)
    texte = data["texte"]

    if session_id and session:
        partie = get_ou_creer_partie(session, defi, session_id)
        mots_reveles: list[str] = json.loads(getattr(partie, "mots_reveles", "[]"))
        if mots_reveles:
            texte = reconstruire_texte(defi.texte_caviarde, mots_reveles)

    return DefiLancement(
        date=defi.date_publication,
        texte_caviarde=texte,
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


def _cached_json(content, max_age: int):
    return JSONResponse(
        content=content,
        headers={"Cache-Control": f"public, max-age={max_age}, s-maxage={max_age}"},
    )


@router.get("/aujourdhui")
async def defi_du_jour(
    session_id: str | None = Query(None),
    session: Session = Depends(get_session),
):
    defi = _get_defi_or_404(session)
    return _cached_json(_build_defi_lancement(defi, session, session_id).model_dump(mode="json"), 60)


@router.get("/historique")
async def historique_defis(session: Session = Depends(get_session)):
    data = [DefiResume(**d).model_dump(mode="json") for d in get_historique_defis(session)]
    return _cached_json(data, 3600)


@router.get("/{date}")
async def defi_par_date(
    date: str,
    session_id: str | None = Query(None),
    session: Session = Depends(get_session),
):
    defi = _get_defi_or_404(session, date)
    return _cached_json(_build_defi_lancement(defi, session, session_id).model_dump(mode="json"), 3600)


@router.get("/aujourdhui/partie", response_model=PartieEtat)
async def etat_partie(session_id: str = Query(...), session: Session = Depends(get_session)):
    defi = _get_defi_or_404(session)
    etat = get_partie_etat(session, defi, session_id)
    if etat.get("mots_reveles"):
        etat["texte_mis_a_jour"] = reconstruire_texte(defi.texte_caviarde, etat["mots_reveles"])
    return PartieEtat(**etat)


@router.get("/{date}/partie", response_model=PartieEtat)
async def etat_partie_date(
    date: str, session_id: str = Query(...), session: Session = Depends(get_session)
):
    defi = _get_defi_or_404(session, date)
    etat = get_partie_etat(session, defi, session_id)
    if etat.get("mots_reveles"):
        etat["texte_mis_a_jour"] = reconstruire_texte(defi.texte_caviarde, etat["mots_reveles"])
    return PartieEtat(**etat)


@router.post("/aujourdhui/proposer", response_model=ProposerTitreResponse)
@limiter.limit("30/minute")
async def proposer_titre(
    request: Request,
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
        mot_revele=resultat.get("mot_revele"),
        texte_mis_a_jour=resultat.get("texte_mis_a_jour"),
    )


@router.post("/{date}/proposer", response_model=ProposerTitreResponse)
@limiter.limit("30/minute")
async def proposer_titre_date(
    request: Request,
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
        mot_revele=resultat.get("mot_revele"),
        texte_mis_a_jour=resultat.get("texte_mis_a_jour"),
    )


@router.post("/aujourdhui/reveler", response_model=RevelerIndiceResponse)
@limiter.limit("30/minute")
async def reveler_indice_endpoint(
    request: Request,
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
@limiter.limit("30/minute")
async def reveler_indice_date(
    request: Request,
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
