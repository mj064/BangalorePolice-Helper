# AI Parking Intelligence Platform

## Project Name

Bengaluru Illegal Traffic Help

---

# Mission

Build an AI-powered decision support platform for Bangalore Traffic Police.

The system should transform parking violation records into actionable enforcement recommendations.

The platform should answer:

1. Where are illegal parking hotspots?
2. Which hotspots create the highest congestion risk?
3. Which hotspots are likely to emerge next?
4. Where should officers be deployed?

---

# Dataset

Current dataset contains:

* parking violations
* latitude
* longitude
* location
* junction name
* police station
* violation type
* vehicle type
* timestamps

The dataset DOES NOT contain:

* traffic speed
* vehicle counts
* signal timings
* travel time

Therefore:

The platform should estimate congestion risk and NOT claim actual congestion measurement.

---

# Core Modules

## Hotspot Detection

Purpose:

Detect recurring parking violation clusters.

Output:

* hotspot id
* hotspot location
* violation count
* trend

Methods:

* DBSCAN (MVP)
* H3 (Production)

---

## Impact Scoring

Purpose:

Estimate congestion risk.

Metric:

Parking Impact Index (PII)

Formula:

PII =
0.4 × Violation Density +
0.3 × Main Road Parking +
0.2 × Peak Hour Violations +
0.1 × Repeat Violations

Output:

0-100 score

---

## Prediction Engine

Purpose:

Predict future hotspots.

Model:

LightGBM

Features:

* hour
* weekday
* month
* junction
* historical violation count

Output:

Risk probability

---

## Recommendation Engine

Purpose:

Convert analytics into actions.

Output:

* officers required
* tow vehicle requirement
* recommended enforcement window

---

# Technology Stack

Frontend:

* React
* TypeScript
* Tailwind
* Mapbox

Backend:

* FastAPI

Database:

* PostgreSQL
* PostGIS

ML:

* Pandas
* Scikit-Learn
* LightGBM
* H3

---

# Coding Principles

Always:

* Type-safe code
* Clean architecture
* Repository pattern
* Service layer
* Reusable components

Never:

* Hardcode business logic
* Put ML code in controllers
* Mix database code with APIs

---

# Success Criteria

The final demo must answer:

1. Where are hotspots?
2. Which hotspots are highest risk?
3. Which hotspots are likely tomorrow?
4. What action should police take?
