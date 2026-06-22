"""Shared recommendation data loader — loads pre-computed recommendations from JSON."""
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


_RECOMMENDATIONS_PATH = _find_json("recommendations.json")


def get_recommendations() -> list[dict]:
    """Load recommendations from JSON. Never caches errors — retries every call."""
    if not _RECOMMENDATIONS_PATH.exists():
        print(f"RECOMMENDATION_DATA: File not found at {_RECOMMENDATIONS_PATH}")
        return []

    try:
        with open(_RECOMMENDATIONS_PATH, "r") as f:
            data = json.load(f)
        print(f"RECOMMENDATION_DATA: Loaded {len(data)} recommendations from {_RECOMMENDATIONS_PATH}")
        return data
    except Exception as e:
        print(f"RECOMMENDATION_DATA: Error loading recommendations: {e}")
        return []


def clear_cache():
    pass