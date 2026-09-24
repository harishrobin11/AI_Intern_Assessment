import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "SupportIQ"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Data path relative to base dir or absolute
    DATA_PATH: str = str(BASE_DIR / "data" / "support_tickets.csv")
    
    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # API Server Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
