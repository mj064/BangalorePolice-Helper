from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    hotspot_id: str
    hotspot_name: str
    priority: str
    officers: int
    tow_vehicles: int
    deployment_window: str
    reason: str
