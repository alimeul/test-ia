from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas.partie import StatsSession
from app.services.stats_service import calculer_stats_session

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/session", response_model=StatsSession)
async def stats_session(session_id: str = Query(...), session: Session = Depends(get_session)):
    return StatsSession(**calculer_stats_session(session, session_id))
