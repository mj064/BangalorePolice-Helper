from __future__ import annotations

from dataclasses import dataclass

from backend.app.ml.prediction_engine import PredictionModelBundle
from backend.app.schemas.prediction import PredictionResponse


@dataclass
class _PredictionCacheState:
    predictions: list[PredictionResponse] | None = None
    model_bundle: PredictionModelBundle | None = None
    last_metrics: dict[str, float] | None = None


_state = _PredictionCacheState()


def get_cached_predictions() -> list[PredictionResponse] | None:
    return _state.predictions


def get_cached_metrics() -> dict[str, float] | None:
    return _state.last_metrics


def set_prediction_cache(
    predictions: list[PredictionResponse],
    model_bundle: PredictionModelBundle,
    last_metrics: dict[str, float],
) -> None:
    _state.predictions = predictions
    _state.model_bundle = model_bundle
    _state.last_metrics = last_metrics


def clear_prediction_cache() -> None:
    _state.predictions = None
    _state.model_bundle = None
    _state.last_metrics = None


def is_prediction_cache_warmed() -> bool:
    return _state.predictions is not None
