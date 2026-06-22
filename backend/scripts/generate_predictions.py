"""
Pre-compute predictions from hotspots.json and save to predictions.json.
Run this locally before deploying to Render.
Output: data/raw/predictions.json, data/raw/recommendations.json
"""
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data/raw")
HOTSPOTS_PATH = DATA_DIR / "hotspots.json"
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
    print(f"Reading {HOTSPOTS_PATH}...")
    with open(HOTSPOTS_PATH, "r") as f:
        hotspots = json.load(f)
    print(f"  Loaded {len(hotspots)} hotspots")

    predictions = []
    recommendations = []
    for h in hotspots:
        score = h.get("impact_score", 0)
        level = _risk_level(score)

        predictions.append({
            "hotspot_id": h.get("id", h.get("name", "")),
            "hotspot_name": h["name"],
            "risk_score": score,
            "risk_level": level,
            "prediction_horizon": "Next 24 hours",
        })

        # Simple recommendations based on risk level
        if level == "Critical":
            rec = {
                "hotspot_id": h.get("id", h.get("name", "")),
                "hotspot_name": h["name"],
                "priority": "Critical",
                "officers": 3,
                "tow_vehicles": 2,
                "deployment_window": "17:00-20:00",
                "reason": "High impact score and critical next-day risk",
            }
        elif level == "High":
            rec = {
                "hotspot_id": h.get("id", h.get("name", "")),
                "hotspot_name": h["name"],
                "priority": "High",
                "officers": 2,
                "tow_vehicles": 1,
                "deployment_window": "17:00-20:00",
                "reason": "Elevated next-day risk with high or rising hotspot impact",
            }
        elif level == "Medium":
            rec = {
                "hotspot_id": h.get("id", h.get("name", "")),
                "hotspot_name": h["name"],
                "priority": "Medium",
                "officers": 1,
                "tow_vehicles": 1,
                "deployment_window": "08:00-11:00",
                "reason": "Moderate risk or impact warrants targeted morning enforcement",
            }
        else:
            rec = {
                "hotspot_id": h.get("id", h.get("name", "")),
                "hotspot_name": h["name"],
                "priority": "Low",
                "officers": 1,
                "tow_vehicles": 1,
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

    level_counts = Counter(p["risk_level"] for p in predictions)
    print("\nRisk level distribution:")
    for level in ["Critical", "High", "Medium", "Low"]:
        print(f"  {level}: {level_counts.get(level, 0)}")


if __name__ == "__main__":
    main()