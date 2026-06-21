from pydantic import BaseModel

class DashboardSummary(BaseModel):
    total_violations: int
    total_hotspots: int
    high_risk_hotspots: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_violations": 298450,
                "total_hotspots": 124,
                "high_risk_hotspots": 12
            }
        }
    }
