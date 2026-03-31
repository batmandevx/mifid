"""
Application Configuration
=========================
Centralized configuration management using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Regulatory Risk Analysis System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/risk_system.db",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis (for caching and Celery)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "./uploads"
    REPORT_DIR: str = "./reports"
    DATA_DIR: str = "./data"
    
    # Analysis Settings
    DEFAULT_CONFIDENCE_LEVEL: float = 0.99
    DEFAULT_TIME_HORIZON: int = 1
    MAX_TIME_HORIZON: int = 252
    MONTE_CARLO_SIMULATIONS: int = 10000
    
    # Regulatory Settings
    SUPPORTED_REGIMES: List[str] = [
        "basel_iii",
        "frtb",
        "ucits",
        "emir",
        "mifid_ii",
        "crr",
        "solvency_ii"
    ]
    
    # Email (for reports)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # External APIs
    BLOOMBERG_API_KEY: Optional[str] = None
    REFINITIV_API_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """Ensure database directory exists for SQLite."""
        if "sqlite" in v:
            db_path = v.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return v
    
    @validator("UPLOAD_DIR", "REPORT_DIR", "DATA_DIR")
    def create_directories(cls, v):
        """Create required directories."""
        os.makedirs(v, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
