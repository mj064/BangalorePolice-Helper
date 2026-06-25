# Project Handoff

Last updated: 2026-06-18

## Purpose

This document is the operational handoff for any future AI agent or engineer working in this repository. It summarizes the intended product, the real implementation state in the workspace, the known gaps between docs and code, and the highest-value next actions.

## Product Summary

Bengaluru Illegal Traffic Help is an AI-assisted parking intelligence platform for Bengaluru Traffic Police. The system converts historical parking-violation records into:

- illegal parking hotspots
- congestion-risk estimates
- future hotspot predictions
- enforcement recommendations

The current repository is primarily focused on the Sprint 1 MVP:

- ingest the violation dataset
- clean and normalize records
- detect recurring hotspot clusters
- assign a Parking Impact Index
- expose APIs
- visualize results on a dashboard map

## Source Documents Reviewed

This handoff is based on the current repository contents, especially:

- [AGENT_CONTEXT.md](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/AGENT_CONTEXT.md)
- [CURRENT_SPRINT.md](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/CURRENT_SPRINT.md)
- [docs/00_project_vision.md](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs/00_project_vision.md) through [docs/15_demo_plan.md](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs/15_demo_plan.md)
- the implemented backend and frontend application code

## Current Project State

### What exists today

The workspace already contains a substantial Sprint 1 implementation:

- backend FastAPI application
- async SQLAlchemy database layer
- violation and hotspot models
- CSV ingestion pipeline
- DBSCAN hotspot clustering
- Parking Impact Index scoring
- hotspot trend computation
- dashboard summary API
- hotspot list API
- hotspot detail API
- React dashboard UI
- map visualization
- hotspot details panel with charts
- next-day prediction visibility in the dashboard
- enforcement recommendation engine
- enforcement recommendation visibility in the dashboard
- backend automated tests
- verified end-to-end MVP demo flow
- next-day prediction module implemented and verified

### What is not done yet

- PostgreSQL/PostGIS-backed runtime setup
- historical persisted daily hotspot risk snapshots
- persisted LightGBM model artifact on disk (current cache is in-memory, warmed at startup)
- scheduled prediction retraining when source data changes

## Intended Architecture

The docs define this pipeline:

`Violation Dataset -> Feature Engineering -> Hotspot Detection -> Impact Scoring -> Prediction Engine -> Recommendation Engine -> Dashboard`

The target architectural style is:

- FastAPI backend
- service and repository layering
- typed response schemas
- React + TypeScript + Tailwind frontend
- geospatial map dashboard
- PostgreSQL + PostGIS in the target design
- LightGBM for prediction in later phases
- H3 for scalable spatial indexing in later phases

## Actual Architecture In Code

### Backend

Key files:

- [backend/app/main.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/main.py)
- [backend/app/core/config.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/core/config.py)
- [backend/app/core/database.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/core/database.py)
- [backend/app/services/ingestion.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/ingestion.py)
- [backend/app/services/hotspot.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/hotspot.py)
- [backend/app/services/recommendation.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/recommendation.py)
- [backend/app/services/prediction.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/prediction.py)
- [backend/app/services/prediction_cache.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/prediction_cache.py)
- [backend/app/ml/hotspot_detector.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/ml/hotspot_detector.py)

Implemented flow at application startup:

1. create database tables
2. ingest CSV if the `violations` table is empty
3. detect hotspots if the `hotspots` table is empty
4. train the LightGBM model once and warm the in-memory prediction cache
5. serve API routes from cached predictions (no on-demand retraining during demo usage)

Backend layering is real, not just planned:

- API routes call repositories and services
- ML logic is separated from route handlers
- persistence is separated into repositories
- schemas define typed responses
- next-day prediction is implemented in a separate engine/service path and does not modify hotspot detection logic
- enforcement recommendations are implemented as deterministic business rules and do not modify hotspot or prediction behavior

### Frontend

Key files:

- [frontend/src/pages/DashboardPage.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/pages/DashboardPage.tsx)
- [frontend/src/maps/HotspotMap.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/maps/HotspotMap.tsx)
- [frontend/src/components/HotspotList.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/HotspotList.tsx)
- [frontend/src/components/HotspotDetailsPanel.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/HotspotDetailsPanel.tsx)
- [frontend/src/components/KPIStats.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/KPIStats.tsx)
- [frontend/src/components/PredictionKPIStats.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/PredictionKPIStats.tsx)
- [frontend/src/components/PredictionsList.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/PredictionsList.tsx)
- [frontend/src/components/RecommendationsList.tsx](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/components/RecommendationsList.tsx)
- [frontend/src/services/api.ts](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/services/api.ts)

Implemented UI behavior:

- fetch dashboard summary
- fetch hotspot list
- render KPIs
- render hotspot map
- filter and sort hotspot list
- select hotspot from list or map
- fetch hotspot detail
- render vehicle and hourly charts
- render the map successfully in a live browser session
- open the hotspot details panel successfully in a live browser session
- fetch next-day predictions from `GET /api/predictions`
- fetch enforcement recommendations from `GET /api/recommendations`
- render prediction KPI cards for highest predicted risk, predicted high-risk zone count, and average predicted risk
- render `Tomorrow's High-Risk Zones` with Critical red, High orange, Medium yellow, and Low green styling
- select a predicted hotspot and show current impact score, tomorrow risk score, trend, and hotspot detail analytics when available
- render `Recommended Enforcement Actions` with hotspot name, priority, officers, tow vehicles, deployment window, and reason
- color-code recommendation priorities with the existing Critical, High, Medium, and Low palette
- use a single-column operations feed on mobile widths while preserving the map-centric desktop dashboard

### Prediction Module

Key files:

- [backend/app/ml/prediction_engine.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/ml/prediction_engine.py)
- [backend/app/services/prediction.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/prediction.py)
- [backend/app/schemas/prediction.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/schemas/prediction.py)
- [backend/app/api/endpoints/predictions.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/api/endpoints/predictions.py)

Implemented prediction behavior:

- prediction horizon is `Next Day`
- model is a `LightGBM` binary classifier
- training uses a time-based train/validation split
- inference returns probability-derived `risk_score`
- `risk_level` is mapped from the predicted probability score
- model uses stable geographic `zone_id` instead of DBSCAN hotspot IDs
- preferred `zone_id` is H3 cell ID
- fallback `zone_id` is a centroid-derived string when H3 is unavailable
- dashboard consumes prediction output and displays next-day risk alongside current hotspot impact metrics
- LightGBM is trained once during application startup (after ingestion/hotspot detection)
- prediction results are cached in memory via `PredictionCache`
- `GET /api/predictions` and `GET /api/recommendations` serve cached output during demo usage
- `RecommendationService` reads cached predictions directly and does not trigger a second training cycle

### Prediction Cache Architecture

Startup path:

`lifespan -> PredictionService.warm_cache() -> train_model() -> predict_next_day() -> set_prediction_cache()`

Request path:

- `GET /api/predictions` -> `PredictionService.get_predictions()` -> return cached list (or compute once on cache miss)
- `GET /api/recommendations` -> `get_cached_predictions()` -> rule engine (no retrain)

Local benchmark against the workspace SQLite database (259 hotspots):

| Path | Latency |
|------|---------|
| Before: train + predict on every request | ~25.6s |
| After: cached `GET /api/predictions` | <0.001s |
| After: cached `GET /api/recommendations` | ~0.02s |

Model behavior and API response contracts are unchanged; only training/inference scheduling changed.

### Data / Storage

Important reality:

- target docs say PostgreSQL + PostGIS
- actual default runtime uses SQLite
- current database file in workspace: `traffic_help.db`

This is a meaningful divergence. Any next agent must decide whether to preserve SQLite for MVP simplicity or move to the documented Postgres/PostGIS stack.

## Implemented APIs

Current routes:

- `GET /`
- `GET /api/dashboard/summary`
- `GET /api/hotspots`
- `GET /api/hotspots/{id}`
- `GET /api/predictions`
- `GET /api/recommendations`

Current missing routes relative to docs:

- none for the current MVP scope

## What Is Completed

### Backend and ML

- App bootstrap and route registration
- Async DB engine/session setup
- Violation and hotspot ORM models
- Violation repository
- Hotspot repository
- CSV ingestion with:
  - null coordinate filtering
  - numeric coordinate coercion
  - Bangalore bounding-box filtering
  - timestamp parsing
  - string defaulting for missing fields
- DBSCAN hotspot clustering using haversine distance
- Parking Impact Index scoring with documented weights
- Hotspot trend logic using recent vs prior 30-day windows
- Hotspot naming using junction, location, or police station fallback
- Hotspot persistence and replacement flow
- Dashboard summary API
- Hotspot list API
- Hotspot detail API with derived distributions
- Next-day prediction engine with:
  - stable spatial `zone_id`
  - training dataset generation
  - evaluation metrics
  - inference pipeline
  - prediction API
- MVP recommendation engine with:
  - deterministic priority rules
  - officer and tow vehicle allocation
  - deployment window selection
  - operational reason generation
  - recommendation API

### Frontend

- Vite React app scaffold
- Tailwind styling
- Dashboard shell
- KPI summary cards
- Searchable and filterable hotspot list
- Interactive map with severity coloring and hover popup
- Hotspot details panel
- Prediction overview cards
- `Recommended Enforcement Actions` recommendation list
- `Tomorrow's High-Risk Zones` prediction list
- Prediction-aware hotspot details panel state
- Mobile one-column operations feed for narrow viewports
- Recharts visualization for vehicle and hourly distributions

### Testing

- Backend API tests exist and pass
- Backend ML tests exist and pass
- Frontend production build passes
- Live browser verification completed against the running local app
- Live browser verification completed for the prediction cards, prediction list, and prediction detail click-through
- Prediction unit and API tests exist and pass
- Recommendation service and API tests exist and pass
- Recommendation dashboard screenshots were captured for desktop, mobile, and focused mobile layouts under `docs/screenshots/`
- Real-data prediction run against the local SQLite database completed successfully

Verified command:

```powershell
python -m pytest backend
```

Verified command:

```powershell
python -m pytest backend -v
```

Verified command:

```powershell
cd frontend
npm run build
```

## Current Sprint

Current sprint document: [CURRENT_SPRINT.md](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/CURRENT_SPRINT.md)

Sprint 1 goal:

- build the analytics foundation

Sprint 1 deliverables from the plan:

- CSV ingestion pipeline
- data cleaning pipeline
- hotspot detection engine
- hotspot API
- basic dashboard map

Assessment:

- the codebase covers the Sprint 1 MVP deliverables
- the MVP demo path is now verified end-to-end
- next-day prediction is now implemented for the current hotspot zones
- MVP recommendations are now implemented for the current hotspot zones
- remaining work is mostly recommendation caching, operationalization, and architectural follow-through beyond MVP

## Pending Tasks

### Immediate

- confirm startup cache-warming runtime cost is acceptable for repeated demo use (training still happens once at boot)
- update README to match the verified run commands and current stack decisions
- keep `docs/AGENT_PROGRESS.md` and `docs/HANDOFF.md` in sync after future milestones

### Near-term

- align tests and developer commands so they work consistently from expected directories
- decide whether to keep SQLite for MVP or migrate now to PostgreSQL/PostGIS
- add explicit run instructions for backend and frontend
- decide whether startup ingestion/clustering should remain synchronous in app startup

### Post-MVP / Sprint 2+

- persist LightGBM model artifact to disk and invalidate cache when source data changes
- richer deployment planning
- H3 support
- background jobs / scheduled retraining
- production database alignment

## Known Issues and Blockers

### Active issues

- Running `pytest` from `backend/` fails due to module import resolution expecting repository-root execution.
- Frontend production build emits a large bundle warning from Vite, but the build succeeds and the demo flow works.
- Prediction training still runs synchronously during startup; large datasets add boot time before APIs are demo-ready.
- Cached predictions are in-memory only; restarting the API requires retraining unless a persisted model artifact is added later.

### Non-blocking but important gaps

- Docs and runtime stack disagree on database choice.
- Docs mention Mapbox, while implementation uses MapLibre.
- Historical docs may still describe recommendation work as future, but the MVP service/schema/API/dashboard section now exists.
- `docs/AGENT_PROGRESS.md` was previously stale and did not reflect the actual implementation state.

### Production Issues and UX Fixes (2026-06-21)

- **Issue 1 - Search Not Working Properly**:
  - Root cause: `frontend/src/components/HotspotList.tsx` only filtered by `h.name` with no debounce and no support for ID/junction partial matches.
  - Fix: added 300ms debounced search matching hotspot ID, name, and junction name with live result count badge.
- **Issue 2 - Hotspot Zones Missing After Reload**:
  - Root cause: convex hull polygon was stored as a JSON string but map source only created Point features, so polygon layers had no real geometry to render.
  - Fix: `frontend/src/maps/HotspotMap.tsx` now builds separate Polygon features from `h.polygon` alongside Point features.
- **Issue 2 - Vehicle Distribution Appears Incorrect**:
  - Root cause: `backend/app/api/endpoints/hotspots.py` used a 0.001 degree bounding box (~111m) and then filtered violations by haversine ≤100m, capturing only a tiny subset of cluster violations (e.g., 9 vs total 63,678).
  - Fix: expanded bounding box to 0.002 degrees (~222m) and removed the redundant haversine filter; distributions now cover the full DBSCAN cluster area.
- **Issue 3 - Hotspot Zones Not Visible On Map**:
  - Root cause: only point markers were rendered; no polygon layer existed.
  - Fix: added `polygon` column to `Hotspot` model, convex hull generation via `scipy.spatial.ConvexHull` in `backend/app/ml/hotspot_detector.py`, GeoJSON fill and outline layers in `frontend/src/maps/HotspotMap.tsx` with risk-level color mapping. Polygon click selects the hotspot.
- **Issue 4 - Data Consistency Validation**:
  - Reviewed hotspot counts, impact scores, and distributions. Impact scores already used full cluster data. Distribution totals now match hotspot violation counts after Issue 2 fix.
- **Additional UX fixes**: polygon parsing fixed for reload persistence, selection state made robust for both point and polygon features, predictions/recommendations lazy-loaded for faster initial render, Command Center search added, risk outlook moved to header as Top 5 Risk Outlook replacing LIVE indicator, light/dark map theme toggle added with localStorage persistence using Google Maps-like Carto basemaps (Voyager light / Dark Matter dark), style.load listener re-adds hotspot layers after theme switches so overlays never disappear, drill-down dimming applied to unselected hotspots, deployment search added to Top Priority Deployments panel.

## Recommended Next Steps

1. Push repository to GitHub using the commands in `docs/DEPLOYMENT.md`.
2. Deploy backend to Render using `render.yaml` and verify `/health` endpoint.
3. Deploy frontend to Vercel using `vercel.json` and set `VITE_API_BASE_URL`.
4. Run end-to-end smoke test against deployed URLs.
5. Decide whether to persist the warmed LightGBM model artifact to disk for faster restarts.
6. Choose one of these strategic paths:
   - stabilize MVP on SQLite + current APIs and add cache invalidation when data changes
   - align infrastructure first to PostgreSQL/PostGIS and H3 before new feature work

Recommended default: stabilize and document the current MVP first. Prediction/recommendation demo latency is now addressed via startup cache warming.

## Prediction Model Feature Engineering & Threshold Optimisation (2026-06-21)

Full ablation study conducted before implementation. Only changes that passed decision criteria were committed.

### Changes to `backend/app/ml/prediction_engine.py`

- `violations_vs_zone_mean` added as 9th feature: ratio of today's violation count to the zone's own expanding historical mean (computed with `shift(1)` — no leakage). Reduces `zone_id_code` importance from 22.1% to 13.2%, helping the model generalise beyond known chronic zones.
- `self.inference_threshold = 0.4` replaces hardcoded `0.5` in `train_model`. Recall improves from 69.3% to 80.7% — 73 fewer missed dangerous zone-days per validation cycle.
- Stored `metrics` dict now includes `"threshold"` key.

### Features NOT implemented (reverted after ablation)

- `is_weekend`: zero importance, zero metric change on this dataset.
- `zone_avg_daily_violations`: caused −1.13pp ROC-AUC with no recall benefit when combined with `violations_vs_zone_mean`. The ratio feature already captures zone-relative context.

### Before vs After

| Metric | Baseline@0.5 | After@0.4 | Delta |
|--------|-------------|-----------|-------|
| ROC-AUC | 0.7805 | 0.7741 | −0.64pp |
| Precision | 50.2% | 44.7% | −5.5pp |
| Recall | 69.3% | **80.7%** | **+11.4pp** |
| F1 | 58.3% | 57.6% | −0.7pp |
| zone_id importance | 22.1% | 13.2% | −8.9pp |

## Classification Threshold Recalibration (2026-06-21)

The PII score → classification label mapping was recalibrated to provide balanced

### Before

| Label    | Range   | Count (259 hotspots) |
|----------|---------|----------------------|
| Low      | ≤ 40    | 16                   |
| Medium   | 41–60   | 382                  |
| High     | 61–80   | 23                   |
| Critical | ≥ 81    | 0                    |

### After

| Label    | Range   | Count (259 hotspots) |
|----------|---------|----------------------|
| Low      | ≤ 45    | 147                  |
| Medium   | 46–55   | 213                  |
| High     | 56–65   | 56                   |
| Critical | ≥ 66    | 5                    |

### Files changed

- `backend/app/repositories/hotspot.py` — `get_high_risk_count` threshold: ≥61 → ≥56
- `backend/app/schemas/hotspot.py` — added `classification` computed field on `HotspotResponse` and `HotspotDetailResponse`
- `frontend/src/utils/risk.ts` — `getRiskAppearanceFromScore` break points updated
- `frontend/src/components/HotspotList.tsx` — badge and filter category thresholds updated
- `frontend/src/maps/HotspotMap.tsx` — three `['step', ...]` expressions (circle, fill, line) updated
- `docs/05_impact_scoring.md` — categories section updated with rationale

### What was NOT changed

- DBSCAN parameters
- PII formula or sub-score weights
- Prediction model
- Recommendation model
- Any raw violation or hotspot data in the database

## Assumptions That Shape The Current System

- Illegal parking is being used as a proxy for congestion risk.
- The system must not claim direct congestion measurement because the dataset lacks speed, flow, and travel-time telemetry.
- Bangalore filtering is approximated with a geographic bounding box during ingestion.
- Hotspots are defined spatially by DBSCAN with an approximately 100 meter epsilon and a minimum sample threshold.
- Hotspot detail distributions are computed from violations within a 0.002 degree bounding box of the hotspot centroid (~222m), not from an explicit hotspot-membership table.
- The current startup process assumes ingestion and hotspot generation can happen synchronously when the API boots.
- The current implementation assumes one main raw CSV source configured by `DATA_CSV_PATH`.
- The prediction label is inferred from next-day zone activity because historical per-day hotspot impact scores are not stored.
- The prediction model is area-based through stable `zone_id`, not DBSCAN-ID based.
- Recommendation logic is deterministic business logic, not machine learning.

## Future Roadmap

### Product roadmap from docs

- impact-scored hotspot dashboard
- hotspot prediction
- officer deployment recommendations
- scalable spatial indexing
- richer operational analytics

### Technical roadmap suggested by current code state

- keep frontend build green as prediction and recommendation UI expands
- verify full local run path
- improve startup/job orchestration
- cache recommendation output if the dashboard needs faster demo startup
- decide on a long-term database strategy
- migrate to PostgreSQL/PostGIS if the project is moving beyond MVP demos
- add H3 indexing when cluster persistence and forecast features need scale

## Run / Verify Notes For The Next Agent

Useful commands already validated:

```powershell
python -m pytest backend
```

```powershell
python -m pytest backend -v
```

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

```powershell
cd frontend
npm run build
```

Commands that still need follow-up:

```powershell
cd backend
pytest
```

Current result:

- backend tests pass from repo root
- frontend build passes
- dashboard summary cards render
- dashboard prediction cards render
- `Tomorrow's High-Risk Zones` renders
- selecting a predicted hotspot opens the forecast detail panel
- hotspot map renders
- hotspot detail panel works
- prediction engine returns next-day predictions for all current hotspots

## Handoff Guidance

If another agent picks this up, do not rely only on the planning docs. The implementation is ahead of several status documents. Treat the source code as authoritative for current behavior, and use the docs as intended design context.

The most useful immediate contribution is to preserve the verified MVP + prediction state and then decide whether the next milestone is:

- product capability expansion, or
- infrastructure alignment with the original architecture docs


Final thresholds applied:
- Deployments tab (risk_score): Critical >=80, High >=65, Medium >=50, Low <50
- All Zones tab (impact_score): Critical >=60, High >=55, Medium >=49, Low <49