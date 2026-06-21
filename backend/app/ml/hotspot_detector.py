import json
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull
from typing import List, Dict, Any, Optional
from datetime import timedelta


class HotspotDetector:
    def __init__(self, eps_meters: float = 100.0, min_samples: int = 20, max_samples: int = 5000):
        # Convert metres to radians for Earth's radius (~6,371 km)
        self.eps_rad = eps_meters / 6_371_000.0
        self.min_samples = min_samples
        # Limit samples for DBSCAN to prevent OOM on Render free tier (512 MB)
        self.max_samples = max_samples

    # ------------------------------------------------------------------
    # Spatial Clustering
    # ------------------------------------------------------------------
    def detect_clusters(self, violations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs DBSCAN on (lat, lon) pairs using Haversine metric.
        Appends a 'cluster_id' column; noise points get cluster_id == -1.
        Samples violations if count exceeds max_samples to stay under memory limits.
        """
        if violations_df.empty:
            violations_df = violations_df.copy()
            violations_df['cluster_id'] = -1
            return violations_df

        total = len(violations_df)
        if total > self.max_samples:
            import warnings
            warnings.warn(
                f"Sampling {self.max_samples} of {total} violations for DBSCAN "
                f"(max_samples={self.max_samples}). Use detected hotspots from sample."
            )
            violations_df = violations_df.sample(n=self.max_samples, random_state=42)

        # DBSCAN requires coordinates in radians for the haversine metric
        coords = np.radians(violations_df[['latitude', 'longitude']].values)

        db = DBSCAN(
            eps=self.eps_rad,
            min_samples=self.min_samples,
            metric='haversine',
            algorithm='ball_tree'
        )
        violations_df = violations_df.copy()
        violations_df['cluster_id'] = db.fit_predict(coords)
        return violations_df

    # ------------------------------------------------------------------
    # Parking Impact Index (PII) Scoring
    # ------------------------------------------------------------------
    def calculate_pii(
        self,
        cluster_violations: pd.DataFrame,
        max_violations_in_any_cluster: int
    ) -> Dict[str, Any]:
        """
        Calculates the Parking Impact Index (PII) for a single cluster.

        Formula (from docs/05_impact_scoring.md):
            PII = 0.4 × Violation Density
                + 0.3 × Main Road Violations
                + 0.2 × Peak Hour Violations
                + 0.1 × Repeat Violations

        All sub-scores are in the range [0, 100].

        Density uses log-normalisation to prevent outlier clusters from
        making all other clusters score near zero.
        """
        v_count = len(cluster_violations)
        if v_count == 0:
            return {"pii": 0, "density": 0.0, "main_road": 0.0,
                    "peak_hour": 0.0, "repeat": 0.0}

        # ── 1. Violation Density (log-normalised, 0-100) ──────────────
        # Log scale: avoids extreme outliers crushing every other cluster.
        # A cluster with the same count as the max gets 100; min_samples → ~0.
        log_count = np.log1p(v_count)
        log_max   = np.log1p(max_violations_in_any_cluster) if max_violations_in_any_cluster > 0 else 1
        density_score = min((log_count / log_max) * 100, 100.0)

        # ── 2. Main Road Parking (0-100) ──────────────────────────────
        # Percentage of violations occurring on main roads / at junctions.
        main_road_keywords = ["main", "road", "junction", "flyover",
                              "crossing", "circle", "highway", "avenue"]
        location_is_main = cluster_violations['location'].str.lower().apply(
            lambda x: any(kw in str(x) for kw in main_road_keywords)
        )
        junction_is_named = (
            cluster_violations['junction_name'].str.strip().str.lower() != 'no junction'
        )
        main_road_mask = location_is_main | junction_is_named
        main_road_score = float(main_road_mask.mean()) * 100

        # ── 3. Peak Hour Violations (0-100) ───────────────────────────
        # Peak morning: 08:00–10:59 | Peak evening: 17:00–19:59
        hours = cluster_violations['created_datetime'].dt.hour
        peak_mask = ((hours >= 8) & (hours <= 10)) | ((hours >= 17) & (hours <= 19))
        peak_hour_score = float(peak_mask.mean()) * 100

        # ── 4. Repeat Violations (0-100) ──────────────────────────────
        # Share of violations where the same vehicle appears more than once.
        unique_vehicles = cluster_violations['vehicle_number'].nunique()
        repeat_ratio = (v_count - unique_vehicles) / v_count if v_count > 0 else 0
        repeat_score = float(repeat_ratio) * 100

        # ── Weighted PII ──────────────────────────────────────────────
        pii = (
            0.4 * density_score +
            0.3 * main_road_score +
            0.2 * peak_hour_score +
            0.1 * repeat_score
        )
        pii = int(min(max(round(pii), 0), 100))

        return {
            "pii": pii,
            "density": round(density_score, 2),
            "main_road": round(main_road_score, 2),
            "peak_hour": round(peak_hour_score, 2),
            "repeat": round(repeat_score, 2),
        }

    # ------------------------------------------------------------------
    # Trend Detection
    # ------------------------------------------------------------------
    def compute_trend(self, cluster_violations: pd.DataFrame) -> str:
        """
        Compares violation counts in the most recent 30-day window vs the
        preceding 30-day window.  Returns 'increasing', 'decreasing', or 'stable'.
        """
        dates = cluster_violations['created_datetime']
        if len(dates) == 0:
            return "stable"

        max_date = dates.max()
        period_start      = max_date - timedelta(days=30)
        prev_period_start = max_date - timedelta(days=60)

        current_count  = int((dates >= period_start).sum())
        previous_count = int(((dates >= prev_period_start) & (dates < period_start)).sum())

        if previous_count == 0:
            return "stable" if current_count == 0 else "increasing"

        ratio = current_count / previous_count
        if ratio >= 1.10:
            return "increasing"
        elif ratio <= 0.90:
            return "decreasing"
        return "stable"

    # ------------------------------------------------------------------
    # Convex Hull Polygon Generation
    # ------------------------------------------------------------------
    def compute_convex_hull(self, cluster_violations: pd.DataFrame) -> Optional[str]:
        """
        Computes a GeoJSON polygon for the cluster using a convex hull
        over the (lon, lat) coordinates. Returns a GeoJSON string or None
        when there aren't enough unique points to form a hull.
        """
        points = cluster_violations[['longitude', 'latitude']].drop_duplicates().values
        if len(points) < 3:
            return None
        try:
            hull = ConvexHull(points)
            hull_coords = points[hull.vertices].tolist()
            # Close the polygon ring for GeoJSON
            hull_coords.append(hull_coords[0])
            geojson = {
                "type": "Polygon",
                "coordinates": [hull_coords]
            }
            return json.dumps(geojson)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Cluster Naming
    # ------------------------------------------------------------------
    def get_cluster_name(self, cluster_violations: pd.DataFrame) -> str:
        """
        Returns a human-readable name for the cluster derived from:
          1. Most common named junction  (preferred)
          2. Most common street prefix from location field
          3. Nearest police station  (fallback)
        """
        # 1. Named junction (exclude 'No Junction')
        junctions = cluster_violations[
            cluster_violations['junction_name'].str.strip().str.lower() != 'no junction'
        ]['junction_name']
        if not junctions.empty:
            return str(junctions.mode().iloc[0])

        # 2. Street name extracted from location column
        locations = cluster_violations['location'].dropna()
        if not locations.empty:
            mode_loc = str(locations.mode().iloc[0])
            parts = mode_loc.split(',')
            short_name = parts[0].strip()
            # If the first segment is very short, append the next part for context
            if len(short_name) < 10 and len(parts) > 1:
                short_name = f"{short_name}, {parts[1].strip()}"
            return short_name

        # 3. Nearest police station
        stations = cluster_violations['police_station'].dropna()
        if not stations.empty:
            return f"Area near {stations.mode().iloc[0]}"

        return "Unknown Hotspot Area"
