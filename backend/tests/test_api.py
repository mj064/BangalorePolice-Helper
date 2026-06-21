import pytest
from datetime import datetime, timedelta, timezone
from backend.app.models.violation import Violation
from backend.app.models.hotspot import Hotspot

@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(client, db_session):
    # Insert mock data
    v1 = Violation(
        id="v1", latitude=12.97, longitude=77.59, location="KR Market",
        vehicle_type="CAR", violation_type="['NO PARKING']", offence_code="[113]",
        created_datetime=datetime.utcnow(), police_station="City Market", junction_name="No Junction"
    )
    h1 = Hotspot(
        id="hotspot_1", name="KR Market Area", latitude=12.97, longitude=77.59,
        violations=10, impact_score=85, violation_density=100.0,
        main_road_score=100.0, peak_hour_score=50.0, repeat_violation_score=20.0,
        trend="stable"
    )
    
    db_session.add(v1)
    db_session.add(h1)
    await db_session.commit()
    
    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_violations"] == 1
    assert data["total_hotspots"] == 1
    assert data["high_risk_hotspots"] == 1 # 85 >= 61

@pytest.mark.asyncio
async def test_get_hotspots_list(client, db_session):
    h1 = Hotspot(
        id="hotspot_1", name="KR Market Area", latitude=12.97, longitude=77.59,
        violations=10, impact_score=85, violation_density=100.0,
        main_road_score=100.0, peak_hour_score=50.0, repeat_violation_score=20.0,
        trend="stable"
    )
    db_session.add(h1)
    await db_session.commit()
    
    response = await client.get("/api/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "hotspot_1"
    assert data[0]["name"] == "KR Market Area"
    assert data[0]["impact_score"] == 85

@pytest.mark.asyncio
async def test_get_hotspot_details(client, db_session):
    h1 = Hotspot(
        id="hotspot_1", name="KR Market Area", latitude=12.97, longitude=77.59,
        violations=10, impact_score=85, violation_density=100.0,
        main_road_score=100.0, peak_hour_score=50.0, repeat_violation_score=20.0,
        trend="stable"
    )
    # Add a violation within 100 meters
    v1 = Violation(
        id="v1", latitude=12.97, longitude=77.59, location="KR Market",
        vehicle_type="CAR", violation_type='["NO PARKING"]', offence_code="[113]",
        created_datetime=datetime(2023, 11, 20, 9, 30, 0), police_station="City Market", junction_name="No Junction"
    )
    
    db_session.add(h1)
    db_session.add(v1)
    await db_session.commit()
    
    response = await client.get("/api/hotspots/hotspot_1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "hotspot_1"
    assert data["trend"] == "stable"
    assert "vehicle_distribution" in data
    assert data["vehicle_distribution"]["CAR"] == 1
    assert data["hourly_distribution"]["9"] == 1
    assert data["violation_type_distribution"]["NO PARKING"] == 1


@pytest.mark.asyncio
async def test_get_predictions_endpoint(client, db_session):
    hotspots = [
        Hotspot(
            id="hotspot_1", name="KR Market", latitude=12.97, longitude=77.59,
            violations=120, impact_score=85, violation_density=100.0,
            main_road_score=90.0, peak_hour_score=60.0, repeat_violation_score=25.0,
            trend="increasing"
        ),
        Hotspot(
            id="hotspot_2", name="Modi Bridge", latitude=12.98, longitude=77.58,
            violations=60, impact_score=55, violation_density=70.0,
            main_road_score=80.0, peak_hour_score=40.0, repeat_violation_score=20.0,
            trend="stable"
        ),
    ]

    base_day = datetime(2024, 1, 1, tzinfo=timezone.utc)
    violations = []

    for day_offset in range(24):
        day = base_day + timedelta(days=day_offset)
        zone_a_count = 6 + (4 if day_offset % 3 == 0 else 0)
        zone_b_count = 2 + (1 if day_offset % 5 == 0 else 0)

        for event_idx in range(zone_a_count):
            violations.append(
                Violation(
                    id=f"zone_a_{day_offset}_{event_idx}",
                    latitude=12.9702,
                    longitude=77.5901,
                    location="KR Market Main Road",
                    vehicle_number=f"KA01A{event_idx}",
                    vehicle_type="CAR",
                    violation_type='["NO PARKING"]',
                    offence_code="[113]",
                    created_datetime=day + timedelta(hours=8 + (event_idx % 3)),
                    police_station="City Market",
                    junction_name="KR Market Junction"
                )
            )

        for event_idx in range(zone_b_count):
            violations.append(
                Violation(
                    id=f"zone_b_{day_offset}_{event_idx}",
                    latitude=12.9802,
                    longitude=77.5802,
                    location="Modi Bridge Road",
                    vehicle_number=f"KA02B{event_idx}",
                    vehicle_type="SCOOTER",
                    violation_type='["WRONG PARKING"]',
                    offence_code="[114]",
                    created_datetime=day + timedelta(hours=10 + (event_idx % 2)),
                    police_station="Cottonpet",
                    junction_name="Modi Bridge Junction"
                )
            )

    db_session.add_all(hotspots + violations)
    await db_session.commit()

    response = await client.get("/api/predictions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert set(data[0].keys()) == {
        "hotspot_id",
        "hotspot_name",
        "risk_score",
        "risk_level",
        "prediction_horizon",
    }
    assert data[0]["prediction_horizon"] == "Next Day"
