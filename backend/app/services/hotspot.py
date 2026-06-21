import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.models.hotspot import Hotspot
from backend.app.repositories.violation import ViolationRepository
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.ml.hotspot_detector import HotspotDetector


class HotspotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.violation_repo = ViolationRepository(db)
        self.hotspot_repo = HotspotRepository(db)
        self.detector = HotspotDetector()

    async def detect_and_save_hotspots(self) -> List[Hotspot]:
        """
        Orchestrates the process of loading violations, clustering them,
        calculating impact scores, and saving the hotspots in the DB.
        """
        # 1. Fetch all violations from the database
        violations = await self.violation_repo.get_all_coordinates_with_features()
        if not violations:
            print("No violations found in database. Cannot run hotspot detection.")
            return []

        # Convert SQLAlchemy ORM objects to a plain Python list of dicts for Pandas
        violations_list = []
        for v in violations:
            violations_list.append({
                "id": v.id,
                "latitude": v.latitude,
                "longitude": v.longitude,
                "location": v.location or "Unknown Location",
                "vehicle_type": v.vehicle_type or "UNKNOWN",
                "created_datetime": v.created_datetime,
                "police_station": v.police_station or "No Police Station",
                "junction_name": v.junction_name or "No Junction",
                # vehicle_number was added to Violation model for repeat-offender scoring
                "vehicle_number": getattr(v, "vehicle_number", "UNKNOWN") or "UNKNOWN",
            })

        df = pd.DataFrame(violations_list)
        df['created_datetime'] = pd.to_datetime(df['created_datetime'], utc=True)

        print(f"Clustering {len(df)} violations with DBSCAN...")
        # 2. Run DBSCAN spatial clustering
        df = self.detector.detect_clusters(df)

        # Filter out noise points (cluster_id == -1)
        clustered = df[df['cluster_id'] != -1]
        cluster_groups = clustered.groupby('cluster_id')

        if len(cluster_groups) == 0:
            print("No hotspots detected by DBSCAN.")
            await self.hotspot_repo.clear_all()
            return []

        cluster_counts = cluster_groups.size()
        max_violations = int(cluster_counts.max()) if not cluster_counts.empty else 1

        hotspots_to_create = []
        hotspot_idx = 1

        print(f"Computing PII scores and polygons for {len(cluster_groups)} clusters (max cluster size: {max_violations})...")
        for cluster_id, cluster_df in cluster_groups:
            centroid_lat = float(cluster_df['latitude'].mean())
            centroid_lon = float(cluster_df['longitude'].mean())
            violation_count = len(cluster_df)

            # Compute Parking Impact Index (PII) and sub-scores
            pii_metrics = self.detector.calculate_pii(cluster_df, max_violations)

            # Compute temporal trend (increasing / stable / decreasing)
            trend_val = self.detector.compute_trend(cluster_df)

            # Derive a human-readable name from junction or street data
            name_val = self.detector.get_cluster_name(cluster_df)

            # Compute convex hull polygon for map visualization
            polygon_val = self.detector.compute_convex_hull(cluster_df)

            hotspot = Hotspot(
                id=f"hotspot_{hotspot_idx}",
                name=name_val,
                latitude=centroid_lat,
                longitude=centroid_lon,
                violations=violation_count,
                impact_score=pii_metrics["pii"],
                violation_density=float(pii_metrics["density"]),
                main_road_score=float(pii_metrics["main_road"]),
                peak_hour_score=float(pii_metrics["peak_hour"]),
                repeat_violation_score=float(pii_metrics["repeat"]),
                trend=trend_val,
                h3_cell="",  # Reserved for future H3 indexing
                polygon=polygon_val
            )
            hotspots_to_create.append(hotspot)
            hotspot_idx += 1

        # 3. Persist results to database
        print(f"Saving {len(hotspots_to_create)} hotspots to database...")
        await self.hotspot_repo.clear_all()
        await self.hotspot_repo.bulk_create(hotspots_to_create)
        print("Hotspots saved successfully!")

        return hotspots_to_create
