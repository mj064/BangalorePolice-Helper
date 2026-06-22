from fastapi import APIRouter
from . import dashboard, health, hotspots, predictions, recommendations

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["hotspots"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

__all__ = ["api_router"]
