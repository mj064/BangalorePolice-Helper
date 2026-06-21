"""
Pre-compute hotspots from the raw CSV and save to a JSON file.
Run this locally before deploying to Render.
Output: data/raw/hotspots.json
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
DATA_CSV = Path("data/raw/jan to may police violation_anonymized791b166.csv")
OUTPUT_JSON = Path("data/raw/hotspots.json")
DB_URL = "sqlite:///./traffic_help.db"
MAX_SAMPLE = 5000   # Match the runtime limit on Render
EPS_METERS = 100.0
MIN_SAMPLES = 20
EPS_RAD = EPS_METERS / 6_371_000.0

# ── Helpers ───────────────────────────────────────────────────────────────────
def haversine_metric(eps_rad, min_samples, algorithm='ball_tree'):
    # DBSCAN will be called via sklearn directly
    pass

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Reading CSV: {DATA_CSV}")
    df = pd.read_csv(DATA_CSV)
    print(f"  Read {len(df)} rows")

    # Parse created_datetime
    df['created_datetime'] = pd.to_datetime(
        df['created_datetime'], format='%Y-%m-%d %H:%M:%S%z', errors='coerce'
    )
    df = df.dropna(subset=['created_datetime', 'latitude', 'longitude'])
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    print(f"  Valid rows: {len(df)}")

    # Sample if necessary
    if len(df) > MAX_SAMPLE:
        df = df.sample(n=MAX_SAMPLE, random_state=42)
        print(f"  Sampled down to {len(df)} for DBSCAN")

    # Cluster with DBSCAN
    from sklearn.cluster import DBSCAN
    coords = np.radians(df[['latitude', 'longitude']].values)
    db = DBSCAN(eps=EPS_RAD, min_samples=MIN_SAMPLES, metric='haversine', algorithm='ball_tree')
    df['cluster_id'] = db.fit_predict(coords)
    print(f"  Clusters found: {df['cluster_id'].nunique()} (including noise=-1)")

    # Compute hotspot features per cluster
    hotspots = []
    for cid, group in df.groupby('cluster_id'):
        if cid == -1:
            continue  # skip noise

        count = len(group)

        # Density score (log-normalised against max cluster size)
        max_count = df[df['cluster_id'] != -1].groupby('cluster_id').size().max() or count
        log_count = np.log1p(count)
        log_max = np.log1p(max_count)
        density_score = min((log_count / log_max) * 100, 100.0)

        # Main road score
        main_road_keywords = ["main", "road", "junction", "flyover",
                              "crossing", "circle", "highway", "avenue"]
        location_is_main = group['location'].str.lower().apply(
            lambda x: any(kw in str(x) for kw in main_road_keywords)
        )
        junction_is_named = (
            group['junction_name'].str.strip().str.lower() != 'no junction'
        )
        main_road_score = float((location_is_main | junction_is_named).mean()) * 100

        # Peak hour score
        hours = group['created_datetime'].dt.hour
        peak_mask = ((hours >= 8) & (hours <= 10)) | ((hours >= 17) & (hours <= 19))
        peak_hour_score = float(peak_mask.mean()) * 100

        # Repeat violation score
        unique_vehicles = group['vehicle_number'].nunique()
        repeat_ratio = (count - unique_vehicles) / count if count > 0 else 0
        repeat_score = float(repeat_ratio) * 100

        # Weighted PII
        pii = int(min(max(round(
            0.4 * density_score + 0.3 * main_road_score +
            0.2 * peak_hour_score + 0.1 * repeat_score
        ), 0), 100))

        # Centroid
        lat = float(group['latitude'].mean())
        lon = float(group['longitude'].mean())

        # Cluster name
        junctions = group[group['junction_name'].str.strip().str.lower() != 'no junction']['junction_name']
        if not junctions.empty:
            name = str(junctions.mode().iloc[0])
        else:
            locations = group['location'].dropna()
            if not locations.empty:
                parts = str(locations.mode().iloc[0]).split(',')
                name = parts[0].strip()
                if len(name) < 10 and len(parts) > 1:
                    name = f"{name}, {parts[1].strip()}"
            else:
                stations = group['police_station'].dropna()
                name = f"Area near {stations.mode().iloc[0]}" if not stations.empty else "Unknown Hotspot Area"

        hotspots.append({
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "violations": int(count),
            "impact_score": pii,
            "violation_density": round(density_score, 2),
            "main_road_score": round(main_road_score, 2),
            "peak_hour_score": round(peak_hour_score, 2),
            "repeat_violation_score": round(repeat_score, 2),
        })

    hotspots.sort(key=lambda h: h['impact_score'], reverse=True)
    print(f"  Generated {len(hotspots)} hotspots")

    # Save
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(hotspots, f, indent=2)
    print(f"Saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()