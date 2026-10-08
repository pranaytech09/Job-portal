from dotenv import load_dotenv
load_dotenv()

import os
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "CareerMatch AI"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # API Keys & Endpoints
    ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "")
    ADZUNA_COUNTRY: str = os.getenv("ADZUNA_COUNTRY", "us")
    
    THE_MUSE_API_KEY: str = os.getenv("THE_MUSE_API_KEY", "")

    # Job pipeline parameters
    DEFAULT_EXPIRY_DAYS: int = int(os.getenv("DEFAULT_EXPIRY_DAYS", "60"))
    URL_VALIDATION_TIMEOUT: float = float(os.getenv("URL_VALIDATION_TIMEOUT", "3.0"))
    MAX_JOBS_PER_SOURCE: int = int(os.getenv("MAX_JOBS_PER_SOURCE", "25"))
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
