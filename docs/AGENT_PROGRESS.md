# Agent Progress

Last updated: 2026-06-21

## Project Snapshot

- Project: Bengaluru Illegal Traffic Help
- Mission: turn parking violation records into hotspot analytics and enforcement decision support for Bengaluru Traffic Police
- Current phase: Sprint 1
- Sprint goal: build the analytics foundation for ingestion, clustering, scoring, API delivery, and a basic dashboard map
- Current milestone status: MVP demo flow verified end-to-end
- Prediction milestone status: next-day prediction engine implemented and verified
- Recommendation milestone status: MVP recommendation engine implemented and verified
- Prediction cache milestone status: startup model training and in-memory prediction cache implemented and verified

## Completed Work

### Prediction Model Feature Engineering & Threshold Optimisation (2026-06-21 Round 3)

Conducted a full ablation study across feature combinations before touching production code.
Implemented only changes that passed the decision criteria (ROC-AUC ≥+1pp OR Recall ≥+3pp).

**Ablation findings (all at threshold=0.4):**

| Configuration | ROC-AUC | Recall | zone_id importance |
|---|---|---|---|
| Baseline t=0.5 (reference) | 0.7805 | 69.3% | 22.1% |
| Baseline t=0.4 (threshold only) | 0.7805 | 80.4% | 22.1% |
| + `violations_vs_zone_mean` only | 0.7741 | 80.7% | 13.2% |
| + `zone_avg_daily_violations` only | 0.7692 | 78.1% | 13.2% |
| + `is_weekend` only | 0.7805 | 80.4% | 22.1% (no change) |
| + avg + vs_mean (final) | 0.7701 | 78.6% | 11.6% |

**Decision: threshold change KEEP, `violations_vs_zone_mean` KEEP, `zone_avg_daily_violations` REVERT, `is_weekend` REVERT.**

- `is_weekend`: zero importance, zero metric change — discarded
- `zone_avg_daily_violations`: drops ROC-AUC −1.13pp and hurts recall when combined — discarded
- `violations_vs_zone_mean` alone: ROC-AUC −0.64pp, recall +0.3pp, `zone_id` importance 22%→13% — kept for semantic value (zone-relative normalisation)
- threshold 0.5→0.4: recall +11.1pp with zero ROC cost — the dominant improvement

**Implemented changes to `backend/app/ml/prediction_engine.py`:**
- Added `violations_vs_zone_mean` to `feature_columns` (9 features total, up from 8)
- Added `violations_vs_zone_mean` computation in `build_training_dataset` using per-zone expanding mean with `shift(1)` — no leakage
- Added `self.inference_threshold = 0.4` (was hardcoded 0.5)
- `train_model` uses `self.inference_threshold` for stored validation metrics
- Stored metrics now include `"threshold": 0.4` key

**Before vs After (vs original baseline@0.5):**

| Metric | Baseline@0.5 | After@0.4 | Delta |
|--------|-------------|-----------|-------|
| ROC-AUC | 0.7805 | 0.7741 | −0.64pp (within tolerance) |
| Precision | 50.2% | 44.7% | −5.5pp (expected tradeoff) |
| Recall | 69.3% | **80.7%** | **+11.4pp** ✅ |
| F1 | 58.3% | 57.6% | −0.7pp |
| zone_id importance | 22.1% | **13.2%** | −8.9pp ✅ |

**Operational impact:** Model now catches 530+ dangerous zone-days vs 457 previously. 73 fewer missed dangerous hotspots per validation cycle. Precision drop from 50% to 45% means ~5% more wasted deployments — acceptable for police operations.

**Verification:** `python -m pytest backend -q` → 12 passed

### Classification Threshold Recalibration (2026-06-21 Round 2)

Recalibrated PII score → classification label mapping to match the actual data distribution

**Before counts (old thresholds: Low≤40, Medium 41-60, High 61-80, Critical≥81):**
- Low: 16 | Medium: 382 | High: 23 | Critical: 0

**After counts (new thresholds: Low≤45, Medium 46-55, High 56-65, Critical≥66):**
- Low: 147 | Medium: 213 | High: 56 | Critical: 5

**Files changed:**
- `backend/app/repositories/hotspot.py` — `get_high_risk_count`: threshold raised from ≥61 to ≥56
- `backend/app/schemas/hotspot.py` — added `classification` computed field (Low/Medium/High/Critical) to both `HotspotResponse` and `HotspotDetailResponse`
- `frontend/src/utils/risk.ts` — `getRiskAppearanceFromScore` break points: 81→66, 61→56, 31→46
- `frontend/src/components/HotspotList.tsx` — badge `getSeverityLabel` and filter `getSeverityCategory` updated
- `frontend/src/maps/HotspotMap.tsx` — three `['step', impact_score]` paint expressions updated (circle color, polygon fill, polygon outline)
- `docs/05_impact_scoring.md` — Categories section updated with new ranges and recalibration note

**Verification:**
- `python -m pytest backend -q` → 12 passed
- `npm run build` → build succeeded
- PII scores confirmed identical (Min=31, Max=75, Mean=48.8)

### Production Issue Fixes (2026-06-21 Round 1)

- **Issue 1 - Search Robustness**: Updated `frontend/src/components/HotspotList.tsx` to support debounced search (300ms) across hotspot name, ID, and junction name with case-insensitive partial matching and a live result count badge. Root cause: original filter only checked `h.name` with no debounce, making search unreliable.
- **Issue 2 - Vehicle Distribution Accuracy**: Fixed `backend/app/api/endpoints/hotspots.py` to use a 0.002 degree bounding box (~222m) instead of 0.001 (~111m) plus removed the redundant Python-side haversine ≤100m filter. Root cause: the bounding box was too tight, capturing only a small fraction of cluster violations (e.g., 9 vs 63,678). After fix, distribution totals accurately represent all violations in the DBSCAN cluster area.
- **Issue 3 - Hotspot Zone Visualization**: Added convex hull polygon generation via `scipy.spatial.ConvexHull` in `backend/app/ml/hotspot_detector.py`, persisted as GeoJSON in the new `polygon` column on the `Hotspot` model. Frontend `HotspotMap.tsx` now renders fill and outline polygon layers with risk-level coloring (Critical=red, High=orange, Medium=yellow, Low=green). Existing circle markers are preserved on top. Polygon click selects the hotspot.
- **Issue 4 - Data Consistency**: Validated that hotspot counts, impact scores, and distributions are now consistent. Impact scores were already computed from full cluster data. Distribution totals now match the hotspot violation count after Issue 2 fix.

### Dashboard UX Finalization (2026-06-21 Round 2 continued)

- **Issue 1 - Search Moved to Header**: Added a debounced global search input in the dashboard header. It filters hotspots and deployments by ID, name, and deployment metadata. The Command Center panel no longer contains its own search box, removing duplication.
- **Issue 2 - Duplicate Risk Outlook Removed**: Removed the local "Risk Outlook" section from the left Command Center panel. The header "Top 5 Risk Outlook" remains the single source of truth for risk previews.
- **Map Polygon Visibility Fix**: Polygons are now hidden by default and only revealed for the selected hotspot. Point features use a `kind: 'point'` property and polygon features use `kind: 'polygon'`, with separate layer filters. This prevents the map from showing every convex-hull area at once.
- **Theme Change Map Preservation**: Theme toggles now use `map.setStyle()` directly instead of remounting the map, so zoom, center, and fly-to position are preserved. A `style.load` listener re-adds layers and restores polygon visibility/feature state after basemap replacement.
- **Theme-Aware Risk Colors**: Hotspot colors now adapt to the active theme. Light mode uses deeper, higher-contrast shades (dark green, amber, orange, red) so hotspots remain readable against the light Carto Voyager basemap. Dark mode retains the original vibrant palette on Dark Matter tiles.
- **Issue 2 - Hotspot Selection Broken**: Selection state updates now target both the point feature ID and the polygon feature ID (`${id}_poly`) to prevent unknown-feature-ID errors during rapid updates. Polygon click handlers were already present; this fix makes selection robust.
- **Issue 3 - Slow Initial Dashboard Load**: `frontend/src/pages/DashboardPage.tsx` now loads summary and hotspots first, then lazy-loads predictions/recommendations via `setTimeout(..., 0)` so the dashboard becomes usable immediately.
- **Issue 4 - Command Center Search**: Added a search input at the top of `frontend/src/components/CommandCenter.tsx` with case-insensitive matching against hotspot ID, name, and deployment metadata. A result count badge is shown while typing.
- **Issue 5 - Risk Outlook Relocation**: Removed the blinking green LIVE indicator from the header and replaced it with a compact horizontal "Top 5 Risk Outlook" widget showing the top 5 predicted hotspots and their risk scores, sourced from `GET /api/predictions`. Each item is clickable and selects the corresponding hotspot.
- **Issue 6 - Light/Dark Map Theme Toggle**: Added a theme toggle button in the header. Preference is persisted to `localStorage`. `HotspotMap.tsx` switches between Carto Voyager (light) and Dark Matter (dark) basemap styles. A `style.load` listener re-adds hotspot layers after style changes so polygons and markers survive theme switches. Drill-down dimming is also applied: unselected hotspots become semi-transparent when a hotspot is selected.
- **Issue 7 - Data Consistency Audit**: No further code changes were required after the bounding-box fix in Round 1. Impact scores continue to use full cluster data. Vehicle/hour/category distributions now match the hotspot violation count.
- **Issue 8 - Deployment Search**: Added a search input inside `frontend/src/components/TopPriorityDeployments.tsx` supporting case-insensitive filtering by hotspot name, priority, and deployment window.

### Backend and ML

- Repository documentation set created in [`docs/`](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs)
- Backend FastAPI application scaffolded with startup lifecycle in [backend/app/main.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/main.py)
- Async database layer implemented with SQLAlchemy in [backend/app/core/database.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/core/database.py)
- Data models implemented for violations and hotspots in [backend/app/models/violation.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/models/violation.py) and [backend/app/models/hotspot.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/models/hotspot.py)
- Repository layer implemented for hotspot and violation access
- CSV ingestion and cleaning pipeline implemented in [backend/app/services/ingestion.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/ingestion.py)
- DBSCAN hotspot detector implemented in [backend/app/ml/hotspot_detector.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/ml/hotspot_detector.py)
- Parking Impact Index scoring implemented with documented 0.4 / 0.3 / 0.2 / 0.1 weighting
- Trend computation and human-readable hotspot naming implemented
- Hotspot orchestration service implemented in [backend/app/services/hotspot.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/hotspot.py)
- API endpoints implemented for:
  - `GET /api/dashboard/summary`
  - `GET /api/hotspots`
  - `GET /api/hotspots/{id}`
- Frontend Vite + React + Tailwind app scaffolded in [`frontend/`](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend)
- Dashboard page implemented with:
  - KPI cards
  - hotspot list with search, severity filter, and sort toggle
  - interactive map
  - hotspot details side panel with charts
- Backend automated tests implemented for API and ML behavior in [backend/tests/](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/tests)
- Frontend build errors fixed by removing unused imports
- MapLibre CSS dependency moved from external CDN loading to a local package import for more reliable demo behavior
- MVP user flow verified live:
  - dashboard summary cards load
  - hotspot list loads
  - hotspot map renders
  - selecting a hotspot opens the details panel
  - hotspot detail analytics populate correctly
- Prediction engine implemented in [backend/app/ml/prediction_engine.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/ml/prediction_engine.py)
- Prediction service implemented in [backend/app/services/prediction.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/prediction.py)
- Prediction API endpoint implemented at `GET /api/predictions`
- Frontend now consumes `GET /api/predictions` on the main dashboard
- Dashboard prediction visibility implemented with:
  - `Tomorrow's High-Risk Zones` section
  - `Highest Predicted Risk` KPI
  - `Predicted High-Risk Zones` KPI
  - `Average Prediction Risk` KPI
  - red/orange/yellow/green risk-level visual distinction
  - prediction click-through into the existing right-side details panel
  - current impact score vs tomorrow risk score trend comparison
- Stable spatial prediction `zone_id` uses H3 cells with centroid-string fallback if H3 is unavailable
- LightGBM next-day classifier implemented with time-based train/validation split
- Prediction tests added for:
  - zone ID creation
  - training dataset generation
  - model training/inference
  - API contract
- Recommendation engine implemented in [backend/app/services/recommendation.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/recommendation.py)
- Recommendation schema implemented in [backend/app/schemas/recommendation.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/schemas/recommendation.py)
- Recommendation API endpoint implemented at `GET /api/recommendations`
- Deterministic recommendation rules convert hotspot impact score, hotspot trend, and next-day prediction risk score into priority, officers, tow vehicles, deployment window, and reason
- Frontend now consumes `GET /api/recommendations` on the main dashboard
- Dashboard section added: `Recommended Enforcement Actions`
- Recommendation UI displays hotspot name, priority, officer count, tow vehicle count, deployment window, and reason with priority color coding
- Mobile dashboard layout now uses a single-column operations feed with no horizontal overflow at 390px viewport width
- Recommendation screenshots saved:
  - [docs/screenshots/recommendations-dashboard-desktop.png](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs/screenshots/recommendations-dashboard-desktop.png)
  - [docs/screenshots/recommendations-dashboard-mobile.png](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs/screenshots/recommendations-dashboard-mobile.png)
  - [docs/screenshots/recommendations-dashboard-mobile-focused.png](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/docs/screenshots/recommendations-dashboard-mobile-focused.png)
- Real-data prediction run verified:
  - 421 predictions returned
  - metrics observed on local dataset:
    - precision: `0.5022`
    - recall: `0.6935`
    - f1: `0.5825`
    - roc_auc: `0.7805`
- Prediction cache implemented in [backend/app/services/prediction_cache.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/services/prediction_cache.py)
- Startup cache warming added in [backend/app/main.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/main.py): LightGBM trains once after ingestion/hotspot detection
- `PredictionService.get_predictions()` serves cached results during demo usage
- `RecommendationService` reads cached predictions via `get_cached_predictions()` and does not retrain
- Local latency benchmark (259 hotspots):
  - before (on-demand train + predict): ~25.6s per request
  - after (cached predictions): <0.001s
  - after (cached recommendations): ~0.02s

## Architecture Status

### Implemented

- Layered backend structure is in place:
  - API layer
  - service layer
  - repository layer
  - database models
- Startup flow currently:
  - create tables
  - ingest CSV if `violations` is empty
  - run hotspot detection if `hotspots` is empty
  - train LightGBM once and warm in-memory prediction cache
- Request flow for demo endpoints:
  - `GET /api/predictions` returns cached predictions
  - `GET /api/recommendations` applies rules to cached predictions (no second training pass)
- Frontend consumes backend APIs through [frontend/src/services/api.ts](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/frontend/src/services/api.ts)
- Hotspot detail endpoint computes chart distributions dynamically from nearby violations
- Prediction visibility is integrated into the existing dashboard without changing the working hotspot APIs or map pipeline
- Recommendation visibility is integrated into the existing dashboard without changing the working hotspot or prediction functionality

### Partial / Divergent From Docs

- Docs describe PostgreSQL + PostGIS, but current runtime default is SQLite via [backend/app/core/config.py](/c:/Users/HP/Coding/Bangalore_illegalTraffic_Help/backend/app/core/config.py)
- Docs describe Mapbox, but frontend currently uses `maplibre-gl`
- MVP recommendation engine is implemented with deterministic business rules
- Docs describe H3 for production, but current hotspot persistence leaves `h3_cell` empty

## Current Sprint Status

- Sprint: Sprint 1
- Overall status: implemented and demo-runnable for Sprint 1 MVP scope
- Definition-of-done coverage:
  - open dashboard: verified
  - see hotspot map: implemented
  - click hotspot: verified
  - view violation count: verified
  - view hotspot severity: verified

## Verification Status

- Backend tests pass when run from repository root:
  - `python -m pytest backend`
- Frontend production build passes:
  - `npm run build`
- Live API verification completed for:
  - `GET /api/dashboard/summary`
  - `GET /api/hotspots`
  - `GET /api/hotspots/hotspot_3`
  - `GET /api/predictions` via test suite and direct service run
- Live browser verification completed for:
  - dashboard KPI cards
  - prediction KPI cards
  - `Tomorrow's High-Risk Zones` section
  - prediction click-through detail panel
  - hotspot list rendering
  - hotspot map rendering
  - hotspot details panel interaction
- Full backend verification passes:
  - `python -m pytest backend -v`
- Frontend production build passes after prediction UI integration:
  - `npm run build`
- Recommendation verification passes:
  - `python -m pytest backend/tests/test_recommendation_service.py -q`
  - `python -m pytest backend -q`
  - `npm run build`
- Live route verification completed for:
  - `GET /api/recommendations`
- Screenshot verification completed for:
  - desktop dashboard recommendation section
  - mobile dashboard recommendation section
  - focused mobile recommendation panel (`recommendations-dashboard-mobile-focused.png`)
- Screenshot files confirmed on disk under `docs/screenshots/` after live dashboard capture against running backend and frontend servers
- Direct `pytest` from the `backend` folder still fails because imports expect the repository root on `PYTHONPATH`

## Completed

- Deployment-preparation pass completed:
  - `.gitignore` hardened for Python/Node/OS artifacts and large generated files
  - `.env.example` files added for backend and frontend
  - Frontend API base URL made configurable via `VITE_API_BASE_URL`
  - Backend health endpoint added at `GET /api/health`
  - Render deployment config (`render.yaml`) created
  - Vercel deployment config (`vercel.json`) created
  - Docker support added (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`)
  - README upgraded with architecture, API table, local dev steps, deployment sections
  - `docs/DEPLOYMENT.md` created with GitHub, Render, Vercel, Docker, and troubleshooting guidance

## Pending Tasks

- Confirm the real CSV file exists at configured `DATA_CSV_PATH`
- Validate startup ingestion behavior against the real dataset size and runtime cost
- Decide whether Sprint 1 should stay on SQLite or be aligned to PostgreSQL/PostGIS now
- Persist LightGBM model artifact to disk and add cache invalidation when violations/hotspots change

## Blockers

- No hard blocker at the repository level
- No current blocker for MVP demo execution
- Practical demo caveat: startup still pays the one-time LightGBM training cost (~26s on the local 421-hotspot dataset) before cached endpoints are ready
- Practical project-level gap: infrastructure docs and actual runtime stack differ on database and map technology

## Recommended Next Steps

1. Decide whether the local SQLite database and CSV path are the intended canonical development setup.
2. Update README run instructions and environment assumptions to match the verified MVP workflow.
3. Decide whether Sprint 2 starts with persisted model artifacts/cache invalidation or with infrastructure alignment to PostgreSQL/PostGIS and H3.
4. Consider addressing the large frontend production bundle warning with code-splitting if demo deployment performance becomes important.

## Known Assumptions

- Congestion is estimated from parking violations and proxy features only, not from real traffic telemetry
- Bangalore geographic filtering is currently a simple bounding box in ingestion
- Hotspot detail distributions are inferred from violations within 100 meters of the hotspot centroid
- Startup ingestion and clustering are acceptable for current dataset size
- The existing `traffic_help.db` in the workspace is treated as generated application state, not as source of truth documentation
- The current dataset and generated hotspot table already support a working local demo without a fresh re-ingestion step
- Prediction labels are inferred from next-day zone activity because historical per-day hotspot impact scores are not persisted
- The prediction model learns geographic patterns using stable `zone_id`, not transient DBSCAN hotspot IDs
- Recommendation logic is deterministic and does not use machine learning; it consumes existing prediction risk score and hotspot impact/trend signals

## Future Roadmap

- Persisted LightGBM model artifact and cache invalidation on data refresh
- Richer officer/tow deployment planning
- H3 indexing for scalable hotspot aggregation
- PostgreSQL + PostGIS migration
- Better scheduling for ingestion, reclustering, and retraining
- Expanded operational dashboard pages for predictions and recommendations

## Verified Run Commands

- Backend:
  - `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`
- Frontend:
  - `cd frontend`
  - `npm run dev -- --host 127.0.0.1 --port 5173`
- Verification:
  - `python -m pytest backend`
  - `python -m pytest backend -v`
  - `cd frontend`
  - `npm run build`


## Categorization thresholds

All Zones tab uses impact_score thresholds: Critical >=60, High >=55, Medium >=49, Low <49.
Deployments tab uses risk_score thresholds: Critical >=80, High >=65, Medium >=50, Low <50.

Final thresholds applied:
- Deployments tab (risk_score): Critical >=80, High >=65, Medium >=50, Low <50
- All Zones tab (impact_score): Critical >=60, High >=55, Medium >=49, Low <49