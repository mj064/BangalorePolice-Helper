import time
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, async_session
from backend.app.api.router import api_router
from backend.app.models.hotspot import Hotspot
from backend.app.services.ingestion import IngestionService
from backend.app.services.hotspot import HotspotService
from backend.app.services.prediction_cache import clear_prediction_cache
from backend.app.repositories.hotspot import HotspotRepository

# ---- lazy data population (runs once on first API call) ----
_populated = False
_populating = False
_PRECOMPUTED_HOTSPOTS = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "hotspots.json"

async def ensure_data_populated():
    """Run ingestion + load pre-computed hotspots once on first API call."""
    global _populated, _populating
    if _populated or _populating:
        return
    _populating = True
    t0 = time.time()
    print("BACKGROUND: Starting data population...")
    import traceback as tb_mod
    try:
        async with async_session() as session:
            t1 = time.time()
            ingestion = IngestionService(session)
            ingested_count = await ingestion.ingest_csv()
            print(f"BACKGROUND: CSV ingestion took {time.time()-t1:.1f}s, ingested={ingested_count}")

            t2 = time.time()
            hotspot_repo = HotspotRepository(session)
            hotspots_count = await hotspot_repo.get_total_count()
            print(f"BACKGROUND: Hotspot count at {time.time()-t2:.1f}s, count={hotspots_count}")

            if hotspots_count == 0 and ingested_count > 0:
                t3 = time.time()
                print("BACKGROUND: Loading pre-computed hotspots.json...")
                import json
                with open(_PRECOMPUTED_HOTSPOTS, "r") as f:
                    precomputed = json.load(f)
                print(f"BACKGROUND: Loaded {len(precomputed)} hotspots from file")
                saved = 0
                for h in precomputed:
                    hotspot = Hotspot(
                        id=str(h.get("id", h.get("name", ""))),
                        name=h["name"],
                        latitude=h["latitude"],
                        longitude=h["longitude"],
                        violations=h["violations"],
                        impact_score=h["impact_score"],
                        violation_density=h.get("violation_density"),
                        main_road_score=h.get("main_road_score"),
                        peak_hour_score=h.get("peak_hour_score"),
                        repeat_violation_score=h.get("repeat_violation_score"),
                    )
                    session.add(hotspot)
                    saved += 1
                await session.commit()
                print(f"BACKGROUND: Saved {saved} hotspots to DB in {time.time()-t3:.1f}s")
            else:
                print(f"BACKGROUND: Skipping hotspot load. count={hotspots_count}, ingested={ingested_count}")

            clear_prediction_cache()
            print("BACKGROUND: Prediction cache cleared")
        print(f"BACKGROUND: Data population complete. Total time: {time.time()-t0:.1f}s")
    except Exception as e:
        print(f"BACKGROUND: Error: {e}")
        tb_mod.print_exc()
    finally:
        _populated = True
        _populating = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal startup — only create tables and verify DB."""
    t0 = time.time()
    print(f"STARTUP [{time.time()-t0:.1f}s]: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text("DROP TABLE IF EXISTS hotspots")))
        await conn.run_sync(Base.metadata.create_all)
    print(f"STARTUP [{time.time()-t0:.1f}s]: Tables created.")

    print(f"STARTUP [{time.time()-t0:.1f}s]: Verifying DB connection...")
    async with async_session() as session:
        try:
            result = await session.execute(text("SELECT 1"))
            print(f"STARTUP [{time.time()-t0:.1f}s]: DB connection OK (SELECT 1 = {result.scalar()})")
        except Exception as e:
            print(f"STARTUP [{time.time()-t0:.1f}s]: DB connection FAILED: {e}")
            raise
    print(f"STARTUP [{time.time()-t0:.1f}s]: Lifespan startup complete.")
    yield
    print("SHUTDOWN: Disposing engine...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": f"Welcome to the {settings.PROJECT_NAME} API. Access docs at /docs."
    }


@app.get("/health")
async def health():
    db_status = "down"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_status = "up"
    except Exception:
        db_status = "down"

    if not _populated and not _populating:
        asyncio.ensure_future(ensure_data_populated())

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "database": db_status,
        "data_populated": _populated,
    }


@app.middleware("http")
async def ensure_data_middleware(request, call_next):
    from fastapi.responses import JSONResponse
    import traceback

    path = request.url.path
    if path in ("/health", "/", "/docs", "/openapi.json") or \
       path.startswith("/api/openapi.json") or path.startswith("/redoc"):
        return await call_next(request)

    if not _populated and not _populating:
        print(f"MIDDLEWARE: Triggering data population (path: {path})")
        try:
            await ensure_data_populated()
        except Exception as e:
            print(f"MIDDLEWARE: Error: {e}")
            traceback.print_exc()
            return JSONResponse(
                status_code=503,
                content={"detail": "Data initialization in progress. Please retry in a few seconds."}
            )

    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)