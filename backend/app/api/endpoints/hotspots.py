from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import json
import math
import numpy as np

from backend.app.core.database import get_db
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.models.violation import Violation
from backend.app.schemas.hotspot import HotspotResponse, HotspotDetailResponse

router = APIRouter()

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great circle distance between two points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

@router.get("", response_model=List[HotspotResponse])
async def get_hotspots(db: AsyncSession = Depends(get_db)):
    """
    Get all illegal parking hotspots ordered by impact score descending.
    """
    repo = HotspotRepository(db)
    return await repo.get_all_ordered()

@router.get("/{id}", response_model=HotspotDetailResponse)
async def get_hotspot_details(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed metrics for a specific hotspot.
    """
    repo = HotspotRepository(db)
    hotspot = await repo.get(id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    # To calculate distributions, fetch violations in the hotspot's geographic area.
    # Use a bounding box (approx 0.002 degrees ~= 222m) to capture the full DBSCAN cluster.
    # The DBSCAN eps is 100m, so cluster members lie within ~200m of the centroid.
    delta = 0.002
    lat_min, lat_max = hotspot.latitude - delta, hotspot.latitude + delta
    lon_min, lon_max = hotspot.longitude - delta, hotspot.longitude + delta

    stmt = select(Violation).filter(
        Violation.latitude >= lat_min,
        Violation.latitude <= lat_max,
        Violation.longitude >= lon_min,
        Violation.longitude <= lon_max
    )
    result = await db.execute(stmt)
    cluster_violations = result.scalars().all()
            
    # Calculate distributions
    vehicle_dist = {}
    violation_type_dist = {}
    hourly_dist = {i: 0 for i in range(24)}
    
    for v in cluster_violations:
        # 1. Vehicle Type
        v_type = v.vehicle_type or "UNKNOWN"
        vehicle_dist[v_type] = vehicle_dist.get(v_type, 0) + 1
        
        # 2. Hourly distribution
        hour = v.created_datetime.hour
        hourly_dist[hour] = hourly_dist.get(hour, 0) + 1
        
        # 3. Violation Type (JSON list of strings)
        try:
            v_types_list = json.loads(v.violation_type)
            if isinstance(v_types_list, list):
                for t in v_types_list:
                    violation_type_dist[t] = violation_type_dist.get(t, 0) + 1
            else:
                violation_type_dist[v.violation_type] = violation_type_dist.get(v.violation_type, 0) + 1
        except Exception:
            # Fallback if parsing fails
            if v.violation_type:
                violation_type_dist[v.violation_type] = violation_type_dist.get(v.violation_type, 0) + 1
                
    # Sort dictionaries by count descending
    vehicle_dist = dict(sorted(vehicle_dist.items(), key=lambda x: x[1], reverse=True))
    violation_type_dist = dict(sorted(violation_type_dist.items(), key=lambda x: x[1], reverse=True))

    return HotspotDetailResponse(
        id=hotspot.id,
        name=hotspot.name,
        latitude=hotspot.latitude,
        longitude=hotspot.longitude,
        violations=hotspot.violations,
        impact_score=hotspot.impact_score,
        violation_density=hotspot.violation_density or 0.0,
        main_road_score=hotspot.main_road_score or 0.0,
        peak_hour_score=hotspot.peak_hour_score or 0.0,
        repeat_violation_score=hotspot.repeat_violation_score or 0.0,
        trend=hotspot.trend,
        h3_cell=hotspot.h3_cell or "",
        vehicle_distribution=vehicle_dist,
        violation_type_distribution=violation_type_dist,
        hourly_distribution=hourly_dist
    )
