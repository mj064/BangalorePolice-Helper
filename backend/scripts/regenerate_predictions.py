"""
Retrain LightGBM next-day predictor on local DB/CSV and regenerate
predictions.json + recommendations.json from the trained model.
Run this locally before deploying to Render.
"""
import json
import os
import sys
from pathlib import Path

# Ensure backend app is importable from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.ml.prediction_engine import PredictionEngine

DATA_DIR = Path("data/raw")
PREDICTIONS_OUTPUT = DATA_DIR / "predictions.json"
RECOMMENDATIONS_OUTPUT = DATA_DIR / "recommendations.json"


def _risk_level(score):
    if score >= 70:
        return "Critical"
    elif score >= 55:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"


def main():
    print("Loading hotspots from JSON...")
    with open(DATA_DIR / "hotspots.json", "r") as f:
        hotspots = json.load(f)
    print(f"  Loaded {len(hotspots)} hotspots")

    # Load violations from SQLite (already populated)
    db_url = "sqlite:///./traffic_help.db"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Loading violations from DB...")
    rows = session.execute(text("SELECT id, created_datetime, latitude, longitude, vehicle_number, vehicle_type, violation_type, location, junction_name, police_station FROM violations"))
    columns = ["id", "created_datetime", "latitude", "longitude",
               "vehicle_number", "vehicle_type", "violation_type",
               "location", "junction_name", "police_station"]
    violations_df = pd.DataFrame(rows.fetchall(), columns=columns)
    print(f"  Loaded {len(violations_df)} violations")

    session.close()

    hotspots_df = pd.DataFrame(hotspots)

    print("Training LightGBM next-day prediction model...")
    engine_ml = PredictionEngine(h3_resolution=9, positive_quantile=0.75)
    training_df = engine_ml.build_training_dataset(violations_df, hotspots_df)
    print(f"  Training rows: {len(training_df)}")

    bundle = engine_ml.train_model(training_df)
    print("  Metrics:", bundle.metrics)

    print("Generating next-day predictions...")
    preds = engine_ml.predict_next_day(hotspots_df, violations_df, bundle)
    print(f"  Predictions: {len(preds)}")
    print("  Risk level counts:", preds["risk_level"].value_counts().to_dict())

    predictions = []
    recommendations = []
    for _, row in preds.iterrows():
        hotspot_id = str(row.get("hotspot_id", ""))
        hotspot_name = str(row.get("hotspot_name", ""))
        risk_score = int(row.get("risk_score", 0))
        risk_level = str(row.get("risk_level", "Low"))
        predictions.append({
            "hotspot_id": hotspot_id,
            "hotspot_name": hotspot_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prediction_horizon": "Next 24 hours",
        })

        if risk_level == "Critical":
            rec = {
                "hotspot_id": hotspot_id,
                "hotspot_name": hotspot_name,
                "priority": "Critical",
                "officers": 3,
                "tow_vehicles": 2,
                "deployment_window": "17:00-20:00",
                "reason": "High impact score and critical next-day risk",
            }
        elif risk_level == "High":
            rec = {
                "hotspot_id": hotspot_id,
                "hotspot_name": hotspot_name,
                "priority": "High",
                "officers": 2,
                "tow_vehicles": 1,
                "deployment_window": "17:00-20:00",
                "reason": "Elevated next-day risk with high or rising hotspot impact",
            }
        elif risk_level == "Medium":
            rec = {
                "hotspot_id": hotspot_id,
                "hotspot_name": hotspot_name,
                "priority": "Medium",
                "officers": 1,
                "tow_vehicles": 1,
                "deployment_window": "08:00-11:00",
                "reason": "Moderate risk or impact warrants targeted morning enforcement",
            }
        else:
            rec = {
                "hotspot_id": hotspot_id,
                "hotspot_name": hotspot_name,
                "priority": "Low",
                "officers": 1,
                "tow_vehicles": 0,
                "deployment_window": "11:00-14:00",
                "reason": "Routine monitoring recommended",
            }
        recommendations.append(rec)

    with open(PREDICTIONS_OUTPUT, "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"Saved {len(predictions)} predictions -> {PREDICTIONS_OUTPUT}")

    with open(RECOMMENDATIONS_OUTPUT, "w") as f:
        json.dump(recommendations, f, indent=2)
    print(f"Saved {len(recommendations)} recommendations -> {RECOMMENDATIONS_OUTPUT}")


if __name__ == "__main__":
    main()