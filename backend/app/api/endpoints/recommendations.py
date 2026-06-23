from fastapi import APIRouter

from backend.app.schemas.recommendation import RecommendationResponse
from backend.app.services.recommendation_data import get_recommendations as load_recommendations

router = APIRouter()


@router.get("", response_model=list[RecommendationResponse])
def get_recommendations():
    try:
        data = load_recommendations()
        return data
    except Exception as e:
        print(f"RECOMMENDATIONS ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []
