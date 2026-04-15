from fastapi import APIRouter
from core.database import ping_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    db_is_up = await ping_db()
    return {
        "status": "ok",
        "database": "connected" if db_is_up else "error"
    }