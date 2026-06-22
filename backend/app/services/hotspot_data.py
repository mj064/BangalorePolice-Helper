"""Shared hotspot data loader — loads pre-computed JSON once."""
import json
from pathlib import Path

_hotspots_cache: list[dict] | None = None
_load_error: str | None = None
_PRECOMPUTED_HOTSPOTS = Path(__file__).parent.parent.parent / "data" / "raw" / "hotspots.json"


def get_hotspots() -> list[dict]:
    global _hotspots_cache, _load_error
    if _hotspots_cache is not None:
        return _hotspots_cache
    if _load_error is not None:
        raise RuntimeError(f"Hotspots previously failed to load: {_load_error}")

    print("BACKGROUND: Loading hotspots from pre-computed JSON...")
    import time as _t
    t0 = _t.time()
    try:
        with open(_PRECOMPUTED_HOTSPOTS, "r") as f:
            data = json.load(f)
        print(f"BACKGROUND: Loaded {len(data)} hotspots from JSON in {_t.time()-t0:.1f}s")
        _hotspots_cache = data
        return data
    except Exception as e:
        _load_error = str(e)
        raise