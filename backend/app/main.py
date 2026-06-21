from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, async_session
from backend.app.api.router import api_router
from backend.app.services.ingestion import IngestionService
from backend.app.services.hotspot import HotspotService
from backend.app.services.prediction import PredictionService
from backend.app.services.prediction_cache import clear_prediction_cache, is_prediction_cache_warmed
from backend.app.repositories.hotspot import HotspotRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB tables
    print("Initializing database tables...")
    async with engine.begin() as conn:
        # Drop and recreate hotspots table when schema changes (e.g. polygon column added)
        await conn.run_sync(lambda c: c.execute(text("DROP TABLE IF EXISTS hotspots")))
        await conn.run_sync(Base.metadata.create_all)
    
    # Run ingestion and clustering in a session
    async with async_session() as session:
        try:
            # 1. Ingest CSV
            ingestion = IngestionService(session)
            ingested_count = await ingestion.ingest_csv()
            
            # 2. Check if hotspots table is empty. If yes, run hotspot detection
            hotspot_repo = HotspotRepository(session)
            hotspots_count = await hotspot_repo.get_total_count()
            
            if hotspots_count == 0 and ingested_count > 0:
                print("Hotspots table is empty. Triggering hotspot detection engine...")
                hotspot_service = HotspotService(session)
                await hotspot_service.detect_and_save_hotspots()
            else:
                print(f"Skipping hotspot detection. Hotspots present: {hotspots_count}")

            # Skip prediction cache warmup on boot to stay under 512 MB on Render free tier.
            # Predictions will be computed on first API call if cache is cold.
            clear_prediction_cache()
            print("Prediction cache cleared. Will warm on first prediction API call.")
        except Exception as e:
            print(f"Error during startup data processing: {e}")
            
    yield
    # Shutdown: Clean up resources
    print("Shutting down engine connection pools...")
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

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
