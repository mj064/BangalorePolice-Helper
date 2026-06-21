# Bengaluru Illegal Traffic Help

AI-powered Parking Intelligence Platform for Bangalore Traffic Police.

## Problem

Illegal parking contributes significantly to traffic congestion.

Traffic police need a way to identify:

* parking hotspots
* congestion risk zones
* future violation hotspots

and deploy enforcement resources effectively.

---

## Solution

The platform provides:

* Hotspot Detection (DBSCAN spatial clustering)
* Impact Scoring (Parking Impact Index — PII)
* Hotspot Prediction (LightGBM next-day risk classifier)
* Enforcement Recommendations (deterministic resource rules)

---

## Architecture

```
Violation Dataset
        ↓
Feature Engineering
        ↓
Hotspot Detection (DBSCAN)
        ↓
Impact Scoring (PII)
        ↓
Prediction Engine (LightGBM)
        ↓
Recommendation Engine
        ↓
Dashboard (React + MapLibre)
```

---

## Tech Stack

Frontend:

* React + TypeScript + Vite
* Tailwind CSS
* MapLibre GL JS + Carto basemaps
* Recharts

Backend:

* FastAPI (async Python + SQLAlchemy)

Database:

* SQLite (development runtime)
* PostgreSQL + PostGIS (target production)

ML / Analytics:

* Pandas
* Scikit-Learn
* LightGBM
* SciPy

---

## Dataset

Input: Bangalore Traffic Police parking violation CSV

Approximate records: ~300,000 violations

Fields:

* Spatial: `latitude`, `longitude`, `location`, `junction_name`, `police_station`
* Temporal: `created_datetime`
* Violation: `violation_type`, `offence_code`
* Vehicle: `vehicle_type`, `vehicle_number`

Limitations: no real-time traffic speed, travel time, or signal timing data.
Congestion risk is estimated from parking violations and proxy features only.

---

## Project Status

Sprint 1 — MVP Complete and deployment-ready.

Verified end-to-end:

* CSV ingestion → data cleaning → hotspot detection → dashboard
* PII scoring and hotspot trend computation
* Next-day prediction via LightGBM
* Enforcement recommendations
* Interactive map and command-center UX
* Production build passes
* Backend tests pass

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health/sanity |
| GET | `/health` | Deployment health check |
| GET | `/api/dashboard/summary` | KPI summary |
| GET | `/api/hotspots` | List hotspots |
| GET | `/api/hotspots/{id}` | Hotspot detail + distributions |
| GET | `/api/predictions` | Next-day risk predictions |
| GET | `/api/recommendations` | Enforcement recommendations |

---

## Local Development

### Requirements

* Python 3.12+
* Node.js 20+
* npm / pnpm / yarn

### Backend

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host --port 5173
```

### Tests

```powershell
python -m pytest backend
```

---

## Deployment

### Render (Backend)

1. Push repository to GitHub.
2. Create a new **Web Service** on Render connected to the repository.
3. Set environment variables:

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./traffic_help.db` |
| `DATA_CSV_PATH` | `data/raw/jan to may police violation_anonymized791b166.csv` |
| `CORS_ORIGINS` | `["https://<your-frontend-domain>"]` |
| `PYTHONPATH` | `.` |

See `render.yaml` for service configuration.

### Vercel (Frontend)

1. Import the `frontend/` project into Vercel.
2. Set the build command to `npm run build`.
3. Set the output directory to `dist`.
4. Add environment variable `VITE_API_BASE_URL` pointing to the Render backend `/api` prefix.

See `vercel.json` for framework routing.

### Docker

```powershell
docker compose up --build
```

* Frontend: `http://localhost`
* Backend: `http://localhost:8000/docs`

---

## Known Limitations

* Runtime database is SQLite; production target is PostgreSQL + PostGIS.
* Predictions and recommendations are generated once at startup and cached in memory.
* `h3_cell` indexing is reserved for future use.
* Startup pays one-time LightGBM training cost (~20–30s on the current dataset).
* Dataset does not include live traffic telemetry.

---

## Roadmap

* Persist LightGBM artifacts and invalidate cache on data change.
* Migrate runtime database to PostgreSQL + PostGIS.
* Add H3 spatial indexing.
* Background jobs for scheduled reclustering and retraining.
* Expand operational analytics beyond MVP.