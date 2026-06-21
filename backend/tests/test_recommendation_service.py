import pytest

from backend.app.models.hotspot import Hotspot
from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.recommendation import RecommendationService


@pytest.mark.asyncio
async def test_recommendation_service_marks_high_impact_critical_risk_as_critical(db_session, monkeypatch):
    hotspot = Hotspot(
        id="hotspot_3",
        name="KR Market Main Road",
        latitude=12.97,
        longitude=77.59,
        violations=125,
        impact_score=74,
        violation_density=100.0,
        main_road_score=90.0,
        peak_hour_score=80.0,
        repeat_violation_score=35.0,
        trend="increasing",
    )
    db_session.add(hotspot)
    await db_session.commit()

    async def fake_predictions(self):
        return [
            PredictionResponse(
                hotspot_id="hotspot_3",
                hotspot_name="KR Market Main Road",
                risk_score=92,
                risk_level="Critical",
            )
        ]

    monkeypatch.setattr(
        "backend.app.services.recommendation.PredictionService.get_predictions",
        fake_predictions,
    )

    recommendations = await RecommendationService(db_session).get_recommendations()

    assert len(recommendations) == 1
    assert recommendations[0].hotspot_id == "hotspot_3"
    assert recommendations[0].hotspot_name == "KR Market Main Road"
    assert recommendations[0].priority == "Critical"
    assert recommendations[0].officers == 3
    assert recommendations[0].tow_vehicles == 2
    assert recommendations[0].deployment_window == "17:00-20:00"
    assert recommendations[0].reason == "High impact score and critical next-day risk"


@pytest.mark.asyncio
async def test_recommendation_service_uses_deterministic_priority_bands(db_session, monkeypatch):
    hotspots = [
        Hotspot(
            id="hotspot_high",
            name="MG Road",
            latitude=12.975,
            longitude=77.61,
            violations=90,
            impact_score=68,
            violation_density=85.0,
            main_road_score=90.0,
            peak_hour_score=60.0,
            repeat_violation_score=20.0,
            trend="increasing",
        ),
        Hotspot(
            id="hotspot_medium",
            name="Indiranagar",
            latitude=12.98,
            longitude=77.64,
            violations=60,
            impact_score=58,
            violation_density=70.0,
            main_road_score=65.0,
            peak_hour_score=45.0,
            repeat_violation_score=10.0,
            trend="stable",
        ),
        Hotspot(
            id="hotspot_low",
            name="Malleshwaram",
            latitude=13.0,
            longitude=77.57,
            violations=25,
            impact_score=28,
            violation_density=25.0,
            main_road_score=30.0,
            peak_hour_score=20.0,
            repeat_violation_score=5.0,
            trend="decreasing",
        ),
    ]
    db_session.add_all(hotspots)
    await db_session.commit()

    async def fake_predictions(self):
        return [
            PredictionResponse(
                hotspot_id="hotspot_high",
                hotspot_name="MG Road",
                risk_score=78,
                risk_level="High",
            ),
            PredictionResponse(
                hotspot_id="hotspot_medium",
                hotspot_name="Indiranagar",
                risk_score=56,
                risk_level="Medium",
            ),
            PredictionResponse(
                hotspot_id="hotspot_low",
                hotspot_name="Malleshwaram",
                risk_score=24,
                risk_level="Low",
            ),
        ]

    monkeypatch.setattr(
        "backend.app.services.recommendation.PredictionService.get_predictions",
        fake_predictions,
    )

    recommendations = await RecommendationService(db_session).get_recommendations()
    by_id = {recommendation.hotspot_id: recommendation for recommendation in recommendations}

    assert [recommendation.priority for recommendation in recommendations] == ["High", "Medium", "Low"]
    assert by_id["hotspot_high"].officers == 2
    assert by_id["hotspot_high"].tow_vehicles == 1
    assert by_id["hotspot_high"].deployment_window == "17:00-20:00"
    assert by_id["hotspot_medium"].officers == 1
    assert by_id["hotspot_medium"].tow_vehicles == 1
    assert by_id["hotspot_medium"].deployment_window == "08:00-11:00"
    assert by_id["hotspot_low"].officers == 1
    assert by_id["hotspot_low"].tow_vehicles == 0


@pytest.mark.asyncio
async def test_get_recommendations_endpoint_returns_action_payload(client, db_session, monkeypatch):
    hotspot = Hotspot(
        id="hotspot_7",
        name="Silk Board Junction",
        latitude=12.917,
        longitude=77.623,
        violations=140,
        impact_score=91,
        violation_density=100.0,
        main_road_score=100.0,
        peak_hour_score=95.0,
        repeat_violation_score=40.0,
        trend="increasing",
    )
    db_session.add(hotspot)
    await db_session.commit()

    async def fake_predictions(self):
        return [
            PredictionResponse(
                hotspot_id="hotspot_7",
                hotspot_name="Silk Board Junction",
                risk_score=94,
                risk_level="Critical",
            )
        ]

    monkeypatch.setattr(
        "backend.app.services.recommendation.PredictionService.get_predictions",
        fake_predictions,
    )

    response = await client.get("/api/recommendations")

    assert response.status_code == 200
    data = response.json()
    assert data == [
        {
            "hotspot_id": "hotspot_7",
            "hotspot_name": "Silk Board Junction",
            "priority": "Critical",
            "officers": 3,
            "tow_vehicles": 2,
            "deployment_window": "17:00-20:00",
            "reason": "High impact score and critical next-day risk",
        }
    ]
