from fastapi import APIRouter, HTTPException
from typing import List
import json
import math
import os
from pathlib import Path

from backend.app.schemas.hotspot import HotspotResponse, HotspotDetailResponse

router = APIRouter()

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

_HOTSPOTS_PATH = _find_json("hotspots.json")

def _load_hotspots() -> List[dict]:
    if not _HOTSPOTS_PATH.exists():
        return []
    try:
        with open(_HOTSPOTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

@router.get("", response_model=List[HotspotResponse])
async def get_hotspots():
    """
    Get all illegal parking hotspots from pre-computed JSON.
    """
    data = _load_hotspots()
    return [
        HotspotResponse(
            id=item.get("id") or item.get("name", ""),
            name=item.get("name", ""),
            latitude=item.get("latitude", 0.0),
            longitude=item.get("longitude", 0.0),
            violations=item.get("violations", 0),
            impact_score=item.get("impact_score", 0),
            polygon=item.get("polygon"),
        )
        for item in data
    ]

@router.get("/{id}", response_model=HotspotDetailResponse)
async def get_hotspot_details(id: str):
    """
    Get detailed metrics for a specific hotspot from pre-computed JSON.
    """
    data = _load_hotspots()
    # Match by id or name to be resilient
    item = next((x for x in data if x.get("id") == id or x.get("name") == id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    return HotspotDetailResponse(
        id=item.get("id") or item.get("name", ""),
        name=item.get("name", ""),
        latitude=item.get("latitude", 0.0),
        longitude=item.get("longitude", 0.0),
        violations=item.get("violations", 0),
        impact_score=item.get("impact_score", 0),
        violation_density=item.get("violation_density", 0.0) or 0.0,
        main_road_score=item.get("main_road_score", 0.0) or 0.0,
        peak_hour_score=item.get("peak_hour_score", 0.0) or 0.0,
        repeat_violation_score=item.get("repeat_violation_score", 0.0) or 0.0,
        trend=item.get("trend", "stable"),
        h3_cell=item.get("h3_cell", ""),
        vehicle_distribution=item.get("vehicle_distribution", {}),
        violation_type_distribution=item.get("violation_type_distribution", {}),
        hourly_distribution=item.get("hourly_distribution", {}),
    )
