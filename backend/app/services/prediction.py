from __future__ import annotations

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ml.prediction_engine import PredictionEngine, PredictionModelBundle
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.repositories.violation import ViolationRepository
from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.prediction_cache import (
    get_cached_metrics,
    get_cached_predictions,
    set_prediction_cache,
)


class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hotspot_repo = HotspotRepository(db)
        self.violation_repo = ViolationRepository(db)
        self.engine = PredictionEngine()

    @property
    def last_metrics(self) -> dict[str, float] | None:
        return get_cached_metrics()

    async def get_predictions(self) -> list[PredictionResponse]:
        cached_predictions = get_cached_predictions()
        if cached_predictions is not None:
            return cached_predictions

        predictions, model_bundle = await self._train_and_predict()
        if predictions:
            set_prediction_cache(predictions, model_bundle, model_bundle.metrics)
            return predictions

        # Fallback: derive simple risk predictions from hotspot impact scores
        hotspots = await self.hotspot_repo.get_all_ordered()
        fallback = []
        for h in hotspots:
            score = h.impact_score or 0
            if score >= 70:
                level = "Critical"
            elif score >= 55:
                level = "High"
            elif score >= 40:
                level = "Medium"
            else:
                level = "Low"
            fallback.append(PredictionResponse(
                hotspot_id=h.id,
                hotspot_name=h.name,
                risk_score=score,
                risk_level=level,
                prediction_horizon="Next 24 hours",
            ))
        return fallback

    async def warm_cache(self) -> list[PredictionResponse]:
        return await self.get_predictions()

    async def _train_and_predict(
        self,
    ) -> tuple[list[PredictionResponse], PredictionModelBundle | None]:
        hotspots = await self.hotspot_repo.get_all_ordered()
        violations = await self.violation_repo.get_all_coordinates_with_features()

        if not hotspots or not violations:
            return [], None

        hotspots_df = pd.DataFrame(
            [
                {
                    "id": hotspot.id,
                    "name": hotspot.name,
                    "latitude": hotspot.latitude,
                    "longitude": hotspot.longitude,
                }
                for hotspot in hotspots
            ]
        )
        violations_df = pd.DataFrame(
            [
                {
                    "id": violation.id,
                    "latitude": violation.latitude,
                    "longitude": violation.longitude,
                    "created_datetime": violation.created_datetime,
                }
                for violation in violations
            ]
        )

        training_df = self.engine.build_training_dataset(violations_df, hotspots_df)
        if training_df.empty:
            return [], None

        model_bundle = self.engine.train_model(training_df)
        prediction_df = self.engine.predict_next_day(hotspots_df, violations_df, model_bundle)

        predictions = [
            PredictionResponse(
                hotspot_id=str(row["hotspot_id"]),
                hotspot_name=str(row["hotspot_name"]),
                risk_score=int(row["risk_score"]),
                risk_level=str(row["risk_level"]),
                prediction_horizon=str(row["prediction_horizon"]),
            )
            for _, row in prediction_df.iterrows()
        ]
        return predictions, model_bundle
