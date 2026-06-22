from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.recommendation import RecommendationResponse
from backend.app.services.recommendation import RecommendationService

router = APIRouter()


@router.get("", response_model=list[RecommendationResponse])
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    service = RecommendationService(db)
    try:
        return await service.get_recommendations()
    except Exception as e:
        print(f"RECOMMENDATIONS ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []
