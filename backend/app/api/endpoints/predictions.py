from fastapi import APIRouter

from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.prediction_data import get_predictions

router = APIRouter()


@router.get("", response_model=list[PredictionResponse])
async def get_predictions():
    try:
        data = get_predictions()
        return data
    except Exception as e:
        print(f"PREDICTIONS ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []
