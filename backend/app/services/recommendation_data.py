"""Shared recommendation data loader — loads pre-computed recommendations from JSON."""
import json
import os
from pathlib import Path

_cache: list[dict] | None = None
_error: str | None = None


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
    global _cache, _error
    if _cache is not None:
        return _cache
    if _error is not None:
        raise RuntimeError(f"Recommendations previously failed to load: {_error}")

    print("BACKGROUND: Loading recommendations from JSON...")
    import time as _t
    t0 = _t.time()
    try:
        with open(_RECOMMENDATIONS_PATH, "r") as f:
            data = json.load(f)
        print(f"BACKGROUND: Loaded {len(data)} recommendations from JSON in {_t.time()-t0:.1f}s")
        _cache = data
        return data
    except Exception as e:
        _error = str(e)
        raise


def clear_cache():
    global _cache, _error
    _cache = None
    _error = None