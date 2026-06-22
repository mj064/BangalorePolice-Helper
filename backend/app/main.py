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
from backend.app.services.hotspot_data import get_hotspots


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal startup — only create tables and verify DB."""
    t0 = __import__('time').time()
    print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: Tables created.")

    print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: Verifying DB connection...")
    async with async_session() as session:
        try:
            result = await session.execute(text("SELECT 1"))
            print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: DB connection OK (SELECT 1 = {result.scalar()})")
        except Exception as e:
            print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: DB connection FAILED: {e}")
            raise
    print(f"STARTUP [{__import__('time').time()-t0:.1f}s]: Lifespan startup complete.")
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

    # Trigger lazy load of hotspots on first call
    try:
        get_hotspots()
    except Exception:
        pass

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "database": db_status,
        "data_populated": True,
    }


@app.middleware("http")
async def load_data_middleware(request, call_next):
    """Lazy-load hotspots from JSON on first data-API call."""
    path = request.url.path
    if path in ("/health", "/", "/docs", "/openapi.json") or \
       path.startswith("/api/openapi.json") or path.startswith("/redoc"):
        return await call_next(request)

    try:
        get_hotspots()
    except Exception as e:
        from fastapi.responses import JSONResponse
        import traceback
        print(f"MIDDLEWARE: Failed to load hotspots: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=503,
            content={"detail": "Data loading failed. Please retry."}
        )

    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)