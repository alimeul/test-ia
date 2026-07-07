from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/defis", tags=["defis"])


@router.get("/aujourdhui")
async def defi_du_jour():
    return {
        "message": "Pas encore implémenté",
        "date": date.today().isoformat(),
    }
