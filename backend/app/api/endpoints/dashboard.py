from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.repositories.violation import ViolationRepository
from backend.app.repositories.hotspot import HotspotRepository
from backend.app.schemas.dashboard import DashboardSummary

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Get high-level summary KPIs for the dashboard.
    """
    violation_repo = ViolationRepository(db)
    hotspot_repo = HotspotRepository(db)
    
    total_violations = await violation_repo.get_total_count()
    total_hotspots = await hotspot_repo.get_total_count()
    high_risk_hotspots = await hotspot_repo.get_high_risk_count()
    
    return DashboardSummary(
        total_violations=total_violations,
        total_hotspots=total_hotspots,
        high_risk_hotspots=high_risk_hotspots
    )
