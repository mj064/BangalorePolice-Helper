from sqlalchemy import Column, String, Float, DateTime, Integer
from backend.app.core.database import Base

class Violation(Base):
    __tablename__ = "violations"

    id = Column(String, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(String, nullable=True)
    vehicle_number = Column(String, nullable=True, index=True)
    vehicle_type = Column(String, nullable=True)
    violation_type = Column(String, nullable=True)  # Serialized JSON array of strings
    offence_code = Column(String, nullable=True)    # Serialized JSON array of integers
    created_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    police_station = Column(String, nullable=True, index=True)
    junction_name = Column(String, nullable=True, index=True)
