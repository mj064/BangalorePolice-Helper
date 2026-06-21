# API Contracts

## Dashboard Summary

GET /api/dashboard/summary

Response:

{
  "total_violations": 0,
  "total_hotspots": 0,
  "high_risk_hotspots": 0
}

---

## Hotspots

GET /api/hotspots

Response:

[
  {
    "id": "hotspot_1",
    "name": "KR Market",
    "latitude": 12.97,
    "longitude": 77.59,
    "violations": 523,
    "impact_score": 94
  }
]

---

GET /api/hotspots/{id}

Returns hotspot details.

---

## Predictions

GET /api/predictions

Returns predicted hotspots.

---

## Recommendations

GET /api/recommendations

Returns enforcement recommendations.