"""Shared hotspot data loader — loads pre-computed JSON once."""
import json
import os
from pathlib import Path

_hotspots_cache: list[dict] | None = None
_load_error: str | None = None


def _find_hotspots_json() -> Path:
    """Try multiple likely locations for the hotspots.json file."""
    cwd = Path.cwd()
    candidates = [
        # If working dir is repo root
        cwd / "data" / "raw" / "hotspots.json",
        # If working dir is backend/ (Render sometimes sets this)
        cwd / "backend" / "data" / "raw" / "hotspots.json",
        # If working dir is one level above repo root
        cwd.parent / "data" / "raw" / "hotspots.json",
        # Environment variable override (most reliable)
        Path(os.environ.get("HOTSPOTS_JSON_PATH", "")),
    ]
    # Filter out empty paths
    candidates = [p for p in candidates if p and not str(p).strip() == ""]
    
    for path in candidates:
        if path.exists():
            return path
    
    # If none found, return the most likely default for error message
    return candidates[0]


_PRECOMPUTED_HOTSPOTS = _find_hotspots_json()


def get_hotspots() -> list[dict]:
    global _hotspots_cache, _load_error
    if _hotspots_cache is not None:
        return _hotspots_cache
    if _load_error is not None:
        raise RuntimeError(f"Hotspots previously failed to load: {_load_error}")

    path = _find_hotspots_json()
    if not path.exists():
        raise FileNotFoundError(f"hotspots.json not found. Looked in: {[str(p) for p in [path]]}")

    print(f"BACKGROUND: Loading hotspots from {path}...")
    import time as _t
    t0 = _t.time()
    try:
        with open(path, "r") as f:
            data = json.load(f)
        print(f"BACKGROUND: Loaded {len(data)} hotspots from JSON in {_t.time()-t0:.1f}s")
        _hotspots_cache = data
        return data
    except Exception as e:
        _load_error = str(e)
        raise
