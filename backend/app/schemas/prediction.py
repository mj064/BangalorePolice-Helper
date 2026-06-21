from pydantic import BaseModel


class PredictionResponse(BaseModel):
    hotspot_id: str
    hotspot_name: str
    risk_score: int
    risk_level: str
    prediction_horizon: str = "Next Day"
