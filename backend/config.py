"""
SportShield Backend — Configuration
Handles all environment settings with validation
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SportShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "sportshield-super-secret-change-in-production"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sportshield.db"
    
    # JWT
    JWT_SECRET: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/avi", "video/mov", "video/mkv"]
    
    # Google Gemini
    GEMINI_API_KEY: str = ""
    
    # Redis (for Celery, optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_ALWAYS_EAGER: bool = False
    
    # SMTP (for Legal Enforcement)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "legal@sportshield.ai"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
