"""Shared prediction data loader — loads pre-computed predictions from JSON."""
import json
import os
from pathlib import Path


def _find_json(filename: str) -> Path:
    cwd = Path.cwd()
    candidates = [
        cwd / "data" / "raw" / filename,
        cwd / "backend" / "data" / "raw" / filename,
        cwd.parent / "data" / "raw" / filename,
        Path(os.environ.get(f"{filename.upper().replace('.','_')}_PATH", "")),
    ]
    candidates = [p for p in candidates if p and not str(p).strip() == ""]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


_PREDICTIONS_PATH = _find_json("predictions.json")


def get_predictions() -> list[dict]:
    """Load predictions from JSON. Never caches errors — retries every call."""
    if not _PREDICTIONS_PATH.exists():
        print(f"PREDICTION_DATA: File not found at {_PREDICTIONS_PATH}")
        return []

    try:
        with open(_PREDICTIONS_PATH, "r") as f:
            data = json.load(f)
        print(f"PREDICTION_DATA: Loaded {len(data)} predictions from {_PREDICTIONS_PATH}")
        return data
    except Exception as e:
        print(f"PREDICTION_DATA: Error loading predictions: {e}")
        return []


def clear_cache():
    pass