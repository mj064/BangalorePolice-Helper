from fastapi import APIRouter
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.services.hotspot_data import get_hotspots

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """
    Get high-level summary KPIs for the dashboard.
    Uses pre-computed hotspot data — no DB queries.
    """
    try:
        hotspots = get_hotspots()
        total_violations = sum(h.get("violations", 0) for h in hotspots)
        total_hotspots = len(hotspots)
        high_risk_hotspots = sum(1 for h in hotspots if (h.get("impact_score") or 0) >= 56)
        
        return DashboardSummary(
            total_violations=total_violations,
            total_hotspots=total_hotspots,
            high_risk_hotspots=high_risk_hotspots
        )
    except Exception as e:
        print(f"DASHBOARD ENDPOINT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return DashboardSummary(
            total_violations=0,
            total_hotspots=0,
            high_risk_hotspots=0
        )
