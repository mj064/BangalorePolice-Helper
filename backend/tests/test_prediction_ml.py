from datetime import datetime, timedelta, timezone

import pandas as pd

from backend.app.ml.prediction_engine import PredictionEngine


def build_hotspots_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"id": "hotspot_1", "name": "KR Market", "latitude": 12.97, "longitude": 77.59},
            {"id": "hotspot_2", "name": "Modi Bridge", "latitude": 12.98, "longitude": 77.58},
        ]
    )


def build_violations_df(days: int = 24) -> pd.DataFrame:
    rows = []
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)

    for day_offset in range(days):
        current_day = start + timedelta(days=day_offset)

        zone_a_count = 6 + (4 if day_offset % 3 == 0 else 0)
        zone_b_count = 2 + (1 if day_offset % 5 == 0 else 0)

        for event_idx in range(zone_a_count):
            rows.append(
                {
                    "id": f"zone_a_{day_offset}_{event_idx}",
                    "latitude": 12.9702,
                    "longitude": 77.5901,
                    "created_datetime": current_day + timedelta(hours=8 + (event_idx % 3)),
                }
            )

        for event_idx in range(zone_b_count):
            rows.append(
                {
                    "id": f"zone_b_{day_offset}_{event_idx}",
                    "latitude": 12.9802,
                    "longitude": 77.5802,
                    "created_datetime": current_day + timedelta(hours=10 + (event_idx % 2)),
                }
            )

    return pd.DataFrame(rows)


def test_prediction_engine_creates_stable_zone_ids():
    engine = PredictionEngine()
    hotspots_df = build_hotspots_df()

    result = engine.attach_zone_ids_to_hotspots(hotspots_df)

    assert "zone_id" in result.columns
    assert result["zone_id"].notna().all()
    assert result["zone_id"].nunique() == 2


def test_prediction_engine_builds_training_rows_and_labels():
    engine = PredictionEngine()
    hotspots_df = build_hotspots_df()
    violations_df = build_violations_df()

    dataset = engine.build_training_dataset(violations_df, hotspots_df)

    assert not dataset.empty
    assert {
        "zone_id",
        "feature_date",
        "hour",
        "weekday",
        "month",
        "historical_violations",
        "label",
    }.issubset(dataset.columns)
    assert set(dataset["label"].unique()).issubset({0, 1})


def test_prediction_engine_trains_and_returns_metrics_and_predictions():
    engine = PredictionEngine()
    hotspots_df = build_hotspots_df()
    violations_df = build_violations_df()

    training_df = engine.build_training_dataset(violations_df, hotspots_df)
    model_bundle = engine.train_model(training_df)
    predictions = engine.predict_next_day(hotspots_df, violations_df, model_bundle)

    assert 0.0 <= model_bundle.metrics["precision"] <= 1.0
    assert 0.0 <= model_bundle.metrics["recall"] <= 1.0
    assert 0.0 <= model_bundle.metrics["f1"] <= 1.0
    assert 0.0 <= model_bundle.metrics["roc_auc"] <= 1.0
    assert not predictions.empty
    assert {
        "hotspot_id",
        "hotspot_name",
        "risk_score",
        "risk_level",
        "prediction_horizon",
    }.issubset(predictions.columns)
    assert set(predictions["prediction_horizon"].unique()) == {"Next Day"}
