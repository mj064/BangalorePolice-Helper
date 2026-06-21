from sqlalchemy import Column, String, Float, Integer
from backend.app.core.database import Base

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    violations = Column(Integer, nullable=False, default=0)
    impact_score = Column(Integer, nullable=False, default=0)  # PII (0-100)
    violation_density = Column(Float, nullable=True)
    main_road_score = Column(Float, nullable=True)
    peak_hour_score = Column(Float, nullable=True)
    repeat_violation_score = Column(Float, nullable=True)
    trend = Column(String, nullable=False, default="stable")
    h3_cell = Column(String, nullable=True)
    polygon = Column(String, nullable=True)  # GeoJSON polygon string for map visualization
