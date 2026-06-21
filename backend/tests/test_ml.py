import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.app.ml.hotspot_detector import HotspotDetector

def test_hotspot_detector_clustering():
    detector = HotspotDetector(eps_meters=100.0, min_samples=2)
    
    # Create mock violations. We place 3 violations close to each other, and 1 far away.
    # Coordinates in Bangalore:
    # Cluster 1 (close to each other)
    # 12.97, 77.59
    # 12.9701, 77.5901 (~15 meters)
    # 12.9699, 77.5899 (~20 meters)
    # Noise (far away)
    # 12.90, 77.50 (~12 km)
    
    data = {
        "id": ["v1", "v2", "v3", "v4"],
        "latitude": [12.97, 12.9701, 12.9699, 12.90],
        "longitude": [77.59, 77.5901, 77.5899, 77.50],
        "location": ["KR Market Main Rd", "KR Market", "KR Market Cross", "Sarjapur Rd"],
        "vehicle_number": ["KA01A1", "KA01B2", "KA01A1", "KA02C3"],
        "vehicle_type": ["CAR", "SCOOTER", "CAR", "CAR"],
        "violation_type": ["['NO PARKING']", "['WRONG PARKING']", "['NO PARKING']", "['NO PARKING']"],
        "created_datetime": [
            datetime.utcnow(),
            datetime.utcnow(),
            datetime.utcnow(),
            datetime.utcnow()
        ],
        "police_station": ["City Market", "City Market", "City Market", "Bellandur"],
        "junction_name": ["BTP082 - KR Market Junction", "BTP082 - KR Market Junction", "No Junction", "No Junction"]
    }
    
    df = pd.DataFrame(data)
    df_clustered = detector.detect_clusters(df)
    
    # We should have cluster 0 for v1, v2, v3 and noise -1 for v4
    assert "cluster_id" in df_clustered.columns
    assert df_clustered.loc[df_clustered['id'] == 'v1', 'cluster_id'].values[0] != -1
    assert df_clustered.loc[df_clustered['id'] == 'v2', 'cluster_id'].values[0] != -1
    assert df_clustered.loc[df_clustered['id'] == 'v3', 'cluster_id'].values[0] != -1
    assert df_clustered.loc[df_clustered['id'] == 'v4', 'cluster_id'].values[0] == -1


def test_hotspot_detector_pii_calculation():
    detector = HotspotDetector(eps_meters=100.0, min_samples=2)
    
    # Create cluster violations
    # We set 4 violations in the cluster
    # 2 are during peak hours (8 AM - 11 AM) -> 50%
    # 2 are on main roads -> 50%
    # 1 repeat vehicle number -> (4 - 3 unique) / 4 = 25%
    data = {
        "id": ["v1", "v2", "v3", "v4"],
        "latitude": [12.97, 12.9701, 12.9702, 12.9703],
        "longitude": [77.59, 77.5901, 77.5902, 77.5903],
        "location": ["KR Market Main Rd", "KR Market Main Rd", "Manasa Layout", "6th Cross"],
        "vehicle_number": ["KA01A1", "KA01A1", "KA01B2", "KA01C3"],
        "vehicle_type": ["CAR", "CAR", "CAR", "CAR"],
        "violation_type": ["['NO PARKING']"] * 4,
        "created_datetime": [
            datetime(2023, 11, 20, 8, 30, 0),  # Peak
            datetime(2023, 11, 20, 9, 0, 0),   # Peak
            datetime(2023, 11, 20, 14, 0, 0),  # Non-peak
            datetime(2023, 11, 20, 15, 0, 0),  # Non-peak
        ],
        "police_station": ["City Market"] * 4,
        "junction_name": ["No Junction", "No Junction", "No Junction", "No Junction"]
    }
    cluster_df = pd.DataFrame(data)
    
    # We pass max_violations = 4 (making density 100%)
    pii_metrics = detector.calculate_pii(cluster_df, max_violations_in_any_cluster=4)
    
    assert pii_metrics["density"] == 100.0
    # Main road: v1 and v2 contain "main" or "road" -> 50%
    assert pii_metrics["main_road"] == 50.0
    # Peak hour: v1, v2 -> 50%
    assert pii_metrics["peak_hour"] == 50.0
    # Repeat: 4 total, 3 unique (KA01A1, KA01B2, KA01C3) -> 25%
    assert pii_metrics["repeat"] == 25.0
    
    # Weighted PII:
    # 0.4 * 100 + 0.3 * 50 + 0.2 * 50 + 0.1 * 25
    # = 40 + 15 + 10 + 2.5 = 67.5 -> rounded to 68
    assert pii_metrics["pii"] == 68
