from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.prediction import PredictionService

router = APIRouter()


@router.get("", response_model=list[PredictionResponse])
async def get_predictions(db: AsyncSession = Depends(get_db)):
    service = PredictionService(db)
    try:
        return await service.get_predictions()
    except Exception as e:
        print(f"PREDICTIONS ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []
