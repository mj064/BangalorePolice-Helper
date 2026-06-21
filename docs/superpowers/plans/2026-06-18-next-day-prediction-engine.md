# Next Day Prediction Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated LightGBM-based prediction module that estimates whether each hotspot zone will become high risk on the following day.

**Architecture:** Use a separate prediction engine that derives a stable `zone_id` from geography rather than DBSCAN hotspot IDs. Aggregate historical violations into daily zone features, train a time-split binary classifier for next-day high-risk probability, and expose predictions through a dedicated API endpoint without modifying the working hotspot pipeline.

**Tech Stack:** FastAPI, SQLAlchemy, Pandas, LightGBM, scikit-learn, optional H3 zone indexing with centroid fallback, pytest

---

### Task 1: Add prediction test coverage first

**Files:**
- Create: `backend/tests/test_prediction_ml.py`
- Modify: `backend/tests/test_api.py`
- Test: `backend/tests/test_prediction_ml.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing ML tests**

```python
import pandas as pd

from backend.app.ml.prediction_engine import PredictionEngine


def test_prediction_engine_creates_stable_zone_ids():
    engine = PredictionEngine()
    hotspots_df = pd.DataFrame(
        [
            {"id": "hotspot_1", "name": "KR Market", "latitude": 12.97, "longitude": 77.59},
            {"id": "hotspot_2", "name": "Modi Bridge", "latitude": 12.98, "longitude": 77.58},
        ]
    )

    result = engine.attach_zone_ids_to_hotspots(hotspots_df)

    assert "zone_id" in result.columns
    assert result["zone_id"].notna().all()
    assert result["zone_id"].nunique() == 2


def test_prediction_engine_builds_training_rows_and_labels():
    engine = PredictionEngine()
    hotspots_df = pd.DataFrame(
        [
            {"id": "hotspot_1", "name": "KR Market", "latitude": 12.97, "longitude": 77.59},
        ]
    )
    violations_df = pd.DataFrame(
        [
            {"id": "v1", "latitude": 12.97, "longitude": 77.59, "created_datetime": "2024-01-01T08:00:00+00:00"},
            {"id": "v2", "latitude": 12.97, "longitude": 77.59, "created_datetime": "2024-01-01T09:00:00+00:00"},
            {"id": "v3", "latitude": 12.97, "longitude": 77.59, "created_datetime": "2024-01-02T08:00:00+00:00"},
            {"id": "v4", "latitude": 12.97, "longitude": 77.59, "created_datetime": "2024-01-03T08:00:00+00:00"},
        ]
    )

    dataset = engine.build_training_dataset(violations_df, hotspots_df)

    assert not dataset.empty
    assert {"zone_id", "feature_date", "hour", "weekday", "month", "historical_violations", "label"}.issubset(dataset.columns)
    assert set(dataset["label"].unique()).issubset({0, 1})


def test_prediction_engine_trains_and_returns_metrics_and_predictions():
    engine = PredictionEngine()
    hotspots_df = pd.DataFrame(
        [
            {"id": "hotspot_1", "name": "KR Market", "latitude": 12.97, "longitude": 77.59},
            {"id": "hotspot_2", "name": "Modi Bridge", "latitude": 12.98, "longitude": 77.58},
        ]
    )

    rows = []
    for day in range(1, 21):
        for idx, base in enumerate([(12.97, 77.59, 6), (12.98, 77.58, 2)], start=1):
            lat, lon, count = base
            day_count = count + (3 if day % 3 == 0 and idx == 1 else 0)
            for event in range(day_count):
                rows.append(
                    {
                        "id": f"v_{idx}_{day}_{event}",
                        "latitude": lat,
                        "longitude": lon,
                        "created_datetime": f"2024-01-{day:02d}T0{event % 9}:00:00+00:00",
                    }
                )
    violations_df = pd.DataFrame(rows)

    training_df = engine.build_training_dataset(violations_df, hotspots_df)
    model_bundle = engine.train_model(training_df)
    predictions = engine.predict_next_day(hotspots_df, violations_df, model_bundle)

    assert 0.0 <= model_bundle.metrics["precision"] <= 1.0
    assert 0.0 <= model_bundle.metrics["recall"] <= 1.0
    assert 0.0 <= model_bundle.metrics["f1"] <= 1.0
    assert "roc_auc" in model_bundle.metrics
    assert not predictions.empty
    assert {"hotspot_id", "hotspot_name", "risk_score", "risk_level", "prediction_horizon"}.issubset(predictions.columns)
```

- [ ] **Step 2: Run ML tests to verify they fail**

Run: `python -m pytest backend/tests/test_prediction_ml.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing prediction engine methods.

- [ ] **Step 3: Write the failing API test**

```python
@pytest.mark.asyncio
async def test_get_predictions_endpoint(client, db_session):
    # create one hotspot plus enough historical violations across multiple days
    # to let the prediction service train and infer
    ...

    response = await client.get("/api/predictions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert set(data[0].keys()) == {
        "hotspot_id",
        "hotspot_name",
        "risk_score",
        "risk_level",
        "prediction_horizon",
    }
    assert data[0]["prediction_horizon"] == "Next Day"
```

- [ ] **Step 4: Run the API prediction test to verify it fails**

Run: `python -m pytest backend/tests/test_api.py::test_get_predictions_endpoint -v`
Expected: FAIL with `404 Not Found` or missing route/service.

### Task 2: Add isolated prediction engine and service

**Files:**
- Create: `backend/app/ml/prediction_engine.py`
- Create: `backend/app/services/prediction.py`
- Create: `backend/app/schemas/prediction.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add model dependencies**

```text
lightgbm==4.5.0
h3==4.1.2
```

- [ ] **Step 2: Implement prediction engine**

Core responsibilities:

```python
class PredictionEngine:
    def attach_zone_ids_to_hotspots(self, hotspots_df: pd.DataFrame) -> pd.DataFrame: ...
    def attach_zone_ids_to_violations(self, violations_df: pd.DataFrame) -> pd.DataFrame: ...
    def build_training_dataset(self, violations_df: pd.DataFrame, hotspots_df: pd.DataFrame) -> pd.DataFrame: ...
    def train_model(self, training_df: pd.DataFrame) -> PredictionModelBundle: ...
    def predict_next_day(self, hotspots_df: pd.DataFrame, violations_df: pd.DataFrame, model_bundle: PredictionModelBundle) -> pd.DataFrame: ...
```

Rules:
- use H3 `zone_id` when available
- fallback to centroid-based string zone ID if H3 import fails
- do not use DBSCAN hotspot IDs as model features
- use time-based split
- output metrics: precision, recall, f1, roc_auc

- [ ] **Step 3: Implement prediction response schemas**

```python
class PredictionResponse(BaseModel):
    hotspot_id: str
    hotspot_name: str
    risk_score: int
    risk_level: str
    prediction_horizon: str = "Next Day"


class PredictionMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    roc_auc: float
```

- [ ] **Step 4: Implement orchestration service**

```python
class PredictionService:
    async def get_predictions(self) -> list[PredictionResponse]:
        # load violations and hotspots
        # build training dataset
        # train model
        # infer next-day predictions
        # map rows into schema instances sorted by risk_score desc
```

- [ ] **Step 5: Run ML tests and verify minimal green**

Run: `python -m pytest backend/tests/test_prediction_ml.py -v`
Expected: PASS

### Task 3: Add prediction API endpoint without touching hotspot behavior

**Files:**
- Create: `backend/app/api/endpoints/predictions.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Implement the endpoint**

```python
router = APIRouter()


@router.get("", response_model=list[PredictionResponse])
async def get_predictions(db: AsyncSession = Depends(get_db)):
    service = PredictionService(db)
    return await service.get_predictions()
```

- [ ] **Step 2: Register the route**

```python
from backend.app.api.endpoints import dashboard, hotspots, predictions

api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
```

- [ ] **Step 3: Finish the API test with real fixture data**

Use 15-20 days of small synthetic violations across at least two geographic zones so the service can train and infer in test runtime.

- [ ] **Step 4: Run API tests**

Run: `python -m pytest backend/tests/test_api.py -v`
Expected: PASS

### Task 4: Update implementation status docs

**Files:**
- Modify: `docs/AGENT_PROGRESS.md`
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Record completed prediction work**

Add:
- prediction engine implemented
- next-day horizon adopted
- stable `zone_id` strategy uses H3 with fallback
- prediction API added
- prediction tests added

- [ ] **Step 2: Record remaining risks**

Add:
- label is inferred from next-day zone activity because historical per-day impact scores are not persisted
- current runtime still trains on demand unless later cached

- [ ] **Step 3: Run full verification**

Run:
- `python -m pytest backend -v`

Expected:
- all existing hotspot tests still pass
- new prediction tests pass
