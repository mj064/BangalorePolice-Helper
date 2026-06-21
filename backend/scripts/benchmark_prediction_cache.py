"""Benchmark prediction/recommendation latency before (train-on-demand) vs after (cache)."""
from __future__ import annotations

import asyncio
import time

from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.core.database import engine
from backend.app.services.prediction import PredictionService
from backend.app.services.prediction_cache import clear_prediction_cache, set_prediction_cache
from backend.app.services.recommendation import RecommendationService


async def main() -> None:
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        prediction_service = PredictionService(session)

        clear_prediction_cache()
        start = time.perf_counter()
        predictions, model_bundle = await prediction_service._train_and_predict()
        train_and_predict_s = time.perf_counter() - start

        if model_bundle is not None:
            set_prediction_cache(predictions, model_bundle, model_bundle.metrics)

        start = time.perf_counter()
        cached_predictions = await prediction_service.get_predictions()
        cached_predictions_s = time.perf_counter() - start

        start = time.perf_counter()
        recommendations = await RecommendationService(session).get_recommendations()
        cached_recommendations_s = time.perf_counter() - start

        print("=== Prediction / Recommendation Latency Benchmark ===")
        print(f"Train + predict (on-demand path): {train_and_predict_s:.3f}s")
        print(f"GET predictions (cached path):      {cached_predictions_s:.3f}s")
        print(f"GET recommendations (cached path):  {cached_recommendations_s:.3f}s")
        print(f"Predictions returned: {len(cached_predictions)}")
        print(f"Recommendations returned: {len(recommendations)}")


if __name__ == "__main__":
    asyncio.run(main())
