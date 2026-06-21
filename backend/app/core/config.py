import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bengaluru Illegal Traffic Help"
    API_PREFIX: str = "/api"
    
    # Database configuration
    # Default to a local SQLite database for ease of portable setup and tests.
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./traffic_help.db",
        validation_alias="DATABASE_URL"
    )
    
    # Path to the raw CSV dataset
    DATA_CSV_PATH: str = Field(
        default="data/raw/jan to may police violation_anonymized791b166.csv",
        validation_alias="DATA_CSV_PATH"
    )
    
    # CORS Configuration — allow Vercel preview + production domains
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
        "https://*.vercel.com",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
