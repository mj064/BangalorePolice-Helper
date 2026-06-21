import time
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, async_session
from backend.app.api.router import api_router
from backend.app.services.ingestion import IngestionService
from backend.app.services.hotspot import HotspotService
from backend.app.services.prediction_cache import clear_prediction_cache
from backend.app.repositories.hotspot import HotspotRepository

# ---- background data population (runs once on first API call, not at startup) ----
_populated = False

async def ensure_data_populated():
    """Run ingestion + hotspot detection once on first API call, not during startup."""
    global _populated
    if _populated:
        return
    t0 = time.time()
    print("BACKGROUND: Starting data population (ingestion + hotspot detection)...")
    import traceback as tb_mod
    try:
        async with async_session() as session:
            # 1. Ingest CSV
            t1 = time.time()
            ingestion = IngestionService(session)
            ingested_count = await ingestion.ingest_csv()
            print(f"BACKGROUND: CSV ingestion took {time.time()-t1:.1f}s, ingested={ingested_count}")

            # 2. Run hotspot detection if table is empty
            t2 = time.time()
            hotspot_repo = HotspotRepository(session)
            hotspots_count = await hotspot_repo.get_total_count()
            print(f"BACKGROUND: Hotspot count check at {time.time()-t2:.1f}s, count={hotspots_count}")

            if hotspots_count == 0 and ingested_count > 0:
                t3 = time.time()
                print("BACKGROUND: Running hotspot detection...")
                hotspot_service = HotspotService(session)
                await hotspot_service.detect_and_save_hotspots()
                print(f"BACKGROUND: Hotspot detection took {time.time()-t3:.1f}s")
            else:
                print(f"BACKGROUND: Skipping hotspot detection. count={hotspots_count}, ingested={ingested_count}")

            clear_prediction_cache()
            print("BACKGROUND: Prediction cache cleared")

        _populated = True
        print(f"BACKGROUND: Data population complete. Total time: {time.time()-t0:.1f}s")
    except MemoryError:
        print(f"BACKGROUND: OUT OF MEMORY during data population. The 512 MB free tier limit was exceeded.")
        print(f"BACKGROUND: Data population FAILED. CSV ingestion or DBSCAN exceeded available memory.")
        print(f"BACKGROUND: Falling back to empty state. Dashboard will show no data.")
    except Exception as e:
        print(f"BACKGROUND: Error during data population: {e}")
        tb_mod.print_exc()
        print(f"BACKGROUND: Data population FAILED. Dashboard will be empty.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal startup — only create tables and verify DB."""
    t0 = time.time()

    # Step 1: Create tables
    print(f"STARTUP [{time.time()-t0:.1f}s]: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text("DROP TABLE IF EXISTS hotspots")))
        await conn.run_sync(Base.metadata.create_all)
    print(f"STARTUP [{time.time()-t0:.1f}s]: Tables created.")

    # Step 2: Verify DB connection works
    print(f"STARTUP [{time.time()-t0:.1f}s]: Verifying DB connection...")
    async with async_session() as session:
        try:
            result = await session.execute(text("SELECT 1"))
            print(f"STARTUP [{time.time()-t0:.1f}s]: DB connection OK (SELECT 1 = {result.scalar()})")
        except Exception as e:
            print(f"STARTUP [{time.time()-t0:.1f}s]: DB connection FAILED: {e}")
            raise
    print(f"STARTUP [{time.time()-t0:.1f}s]: Lifespan startup complete. Yielding FastAPI control.")
    yield

    # Shutdown
    print(f"SHUTDOWN: Disposing engine connection pools...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Set CORS middleware
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
    """Health endpoint — triggers data population on first call."""
    global _populated
    db_status = "down"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_status = "up"
    except Exception:
        db_status = "down"

    # Trigger data population in background (non-blocking)
    if not _populated:
        asyncio.ensure_future(ensure_data_populated())

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "database": db_status,
        "data_populated": _populated,
    }


# Middleware: ensure data is populated before any API endpoint runs
@app.middleware("http")
async def ensure_data_middleware(request, call_next):
    """Ensures data ingestion + hotspot detection runs before API calls."""
    from fastapi.responses import JSONResponse
    import traceback

    # Skip data check for /health and /docs and /openapi.json
    path = request.url.path
    if path in ("/health", "/", "/docs", "/openapi.json") or path.startswith("/api/openapi.json") or path.startswith("/redoc"):
        return await call_next(request)

    # Trigger data population synchronously on the first data-API call
    if not _populated:
        print(f"MIDDLEWARE: Data not populated yet. Triggering population (triggered by: {path})")
        try:
            await ensure_data_populated()
            print("MIDDLEWARE: Data population complete.")
        except Exception as e:
            print(f"MIDDLEWARE: Data population failed: {e}")
            traceback.print_exc()
            return JSONResponse(
                status_code=503,
                content={"detail": "Data initialization in progress. Please retry in a few seconds."}
            )

    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)