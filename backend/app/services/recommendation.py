from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.hotspot import Hotspot
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.schemas.prediction import PredictionResponse
from backend.app.schemas.recommendation import RecommendationResponse
from backend.app.services.prediction import PredictionService
from backend.app.services.prediction_cache import get_cached_predictions


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.hotspot_repo = HotspotRepository(db)
        self.prediction_service = PredictionService(db)

    async def get_recommendations(self) -> list[RecommendationResponse]:
        hotspots = await self.hotspot_repo.get_all_ordered()
        predictions = get_cached_predictions()
        if predictions is None:
            predictions = await self.prediction_service.get_predictions()
        hotspots_by_id = {hotspot.id: hotspot for hotspot in hotspots}

        recommendations = [
            self._build_recommendation(hotspots_by_id[prediction.hotspot_id], prediction)
            for prediction in predictions
            if prediction.hotspot_id in hotspots_by_id
        ]

        return sorted(
            recommendations,
            key=lambda recommendation: (
                self._priority_rank(recommendation.priority),
                recommendation.officers,
                recommendation.tow_vehicles,
            ),
            reverse=True,
        )

    def _build_recommendation(
        self,
        hotspot: Hotspot,
        prediction: PredictionResponse,
    ) -> RecommendationResponse:
        trend = hotspot.trend.lower()

        if prediction.risk_score >= 90 and hotspot.impact_score >= 70:
            return RecommendationResponse(
                hotspot_id=hotspot.id,
                hotspot_name=hotspot.name,
                priority="Critical",
                officers=3,
                tow_vehicles=2,
                deployment_window="17:00-20:00",
                reason="High impact score and critical next-day risk",
            )

        if (
            prediction.risk_score >= 75 and hotspot.impact_score >= 60
        ) or (
            trend == "increasing" and prediction.risk_score >= 70
        ):
            return RecommendationResponse(
                hotspot_id=hotspot.id,
                hotspot_name=hotspot.name,
                priority="High",
                officers=2,
                tow_vehicles=1,
                deployment_window="17:00-20:00",
                reason="Elevated next-day risk with high or rising hotspot impact",
            )

        if prediction.risk_score >= 50 or hotspot.impact_score >= 50:
            return RecommendationResponse(
                hotspot_id=hotspot.id,
                hotspot_name=hotspot.name,
                priority="Medium",
                officers=1,
                tow_vehicles=1,
                deployment_window="08:00-11:00",
                reason="Moderate risk or impact warrants targeted morning enforcement",
            )

        return RecommendationResponse(
            hotspot_id=hotspot.id,
            hotspot_name=hotspot.name,
            priority="Low",
            officers=1,
            tow_vehicles=0,
            deployment_window="11:00-14:00",
            reason="Routine monitoring recommended",
        )

    @staticmethod
    def _priority_rank(priority: str) -> int:
        return {
            "Critical": 4,
            "High": 3,
            "Medium": 2,
            "Low": 1,
        }.get(priority, 0)
