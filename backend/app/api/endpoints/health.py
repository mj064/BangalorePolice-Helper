from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.prediction_cache import is_prediction_cache_warmed

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for readiness probes and deployment monitoring.
    Verifies database connectivity and prediction cache state.
    """
    db_ok = False
    try:
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy",
        "database": "up" if db_ok else "down",
        "prediction_cache_warmed": is_prediction_cache_warmed(),
    }