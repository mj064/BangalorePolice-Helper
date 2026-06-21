# Backend Design

## Framework

FastAPI (async Python)

---

## Responsibilities

* CSV ingestion and data cleaning
* DBSCAN hotspot detection orchestration
* Parking Impact Index (PII) computation
* LightGBM next-day prediction training and inference
* Deterministic enforcement recommendation generation

---

## Layers

API Layer (FastAPI routers)

Service Layer (business logic orchestration)

Repository Layer (data access)

Database Layer (SQLAlchemy ORM)

ML Layer (sklearn / LightGBM / scipy)

---

## Principles

* dependency injection via FastAPI `Depends`
* async endpoints with `AsyncSession`
* typed Pydantic response schemas
* clean architecture (controllers → services → repositories)
* ML code isolated from API controllers

---

## Future Improvements

Background job scheduler for periodic reclustering and model retraining

Persisted model artifacts with cache invalidation on data change
