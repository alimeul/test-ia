from fastapi import APIRouter

router = APIRouter(prefix="/tentatives", tags=["tentatives"])


@router.get("/")
async def lister_tentatives():
    return {"message": "Pas encore implémenté"}
