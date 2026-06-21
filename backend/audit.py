import asyncio
from backend.app.core.database import async_session
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.repositories.violation import ViolationRepository
from sqlalchemy.future import select
from backend.app.models.violation import Violation
import json
import math
import numpy as np

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

async def audit():
    async with async_session() as session:
        h_repo = HotspotRepository(session)
        hotspots = await h_repo.get_all_ordered()
        print(f"Total Hotspots: {len(hotspots)}")
        
        # Test the BTP082 one
        btp082 = next((h for h in hotspots if "BTP082" in h.name), None)
        if btp082:
            print(f"Found {btp082.name} with {btp082.violations} violations in DB.")
            delta = 0.001
            lat_min, lat_max = btp082.latitude - delta, btp082.latitude + delta
            lon_min, lon_max = btp082.longitude - delta, btp082.longitude + delta
            
            stmt = select(Violation).filter(
                Violation.latitude >= lat_min,
                Violation.latitude <= lat_max,
                Violation.longitude >= lon_min,
                Violation.longitude <= lon_max
            )
            result = await session.execute(stmt)
            violations = result.scalars().all()
            cluster_violations = []
            for v in violations:
                dist = haversine_distance(btp082.latitude, btp082.longitude, v.latitude, v.longitude)
                if dist <= 100.0:
                    cluster_violations.append(v)
            print(f"Violations within 100m radius of centroid: {len(cluster_violations)}")
            
        else:
            print("BTP082 not found")
            
        try:
            from scipy.spatial import ConvexHull
            print("scipy.spatial.ConvexHull is available.")
        except ImportError:
            print("scipy not available.")

if __name__ == "__main__":
    asyncio.run(audit())
