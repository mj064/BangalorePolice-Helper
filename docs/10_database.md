# Database Design

## Database

SQLite (development runtime)

PostgreSQL + PostGIS (target production stack)

---

## Table

violations

Fields:

* id
* created_datetime
* latitude
* longitude
* location
* junction_name
* police_station
* violation_type
* vehicle_type
* vehicle_number

---

## Table

hotspots

Fields:

* id
* name
* latitude
* longitude
* violations
* impact_score (PII 0-100)
* violation_density
* main_road_score
* peak_hour_score
* repeat_violation_score
* trend
* h3_cell (reserved for future)
* polygon (GeoJSON convex hull)

---

## Table

predictions (in-memory cache, not persisted)

Fields:

* hotspot_id
* hotspot_name
* risk_score
* risk_level
* prediction_horizon

---

## Table

recommendations (computed from cached predictions)

Fields:

* hotspot_id
* hotspot_name
* priority
* officers
* tow_vehicles
* deployment_window
* reason

---

## Future Improvements

Partitioning

Time-series optimization
