from pydantic import BaseModel, computed_field
from typing import Optional, Dict, List

# ---------------------------------------------------------------------------
# Classification thresholds: PII score → label
# Low  : score <= 45
# Medium: 46 – 55
# High : 56 – 65
# Critical: >= 66
# ---------------------------------------------------------------------------

def _classify_pii(score: int) -> str:
    if score >= 66:
        return "Critical"
    if score >= 56:
        return "High"
    if score >= 46:
        return "Medium"
    return "Low"


class HotspotResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    violations: int
    impact_score: int
    polygon: Optional[str] = None

    @computed_field
    @property
    def classification(self) -> str:
        return _classify_pii(self.impact_score)

    class Config:
        from_attributes = True

class HotspotDetailResponse(HotspotResponse):
    violation_density: float
    main_road_score: float
    peak_hour_score: float
    repeat_violation_score: float
    trend: str
    h3_cell: Optional[str] = ""
    polygon: Optional[str] = None
    
    # Distribution aggregates for the frontend charts
    vehicle_distribution: Dict[str, int] = {}
    violation_type_distribution: Dict[str, int] = {}
    hourly_distribution: Dict[int, int] = {}

    # classification is inherited from HotspotResponse via computed_field

    class Config:
        from_attributes = True
