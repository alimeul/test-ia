from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/")
async def lister_stats():
    return {"message": "Pas encore implémenté"}
