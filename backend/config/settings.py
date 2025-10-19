"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    APP_NAME: str = "IBKR Trading WebApp"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_PORT: int = 8000
    
    # IBKR
    IBKR_ACCOUNT_ID: str
    IBKR_API_BASE_URL: str = "https://127.0.0.1:5055/v1/api"
    IBKR_SSL_VERIFY: bool = False
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    
    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "trading-charts"
    MINIO_SECURE: bool = False
    
    # OpenAI / LLM
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    AI_REQUEST_TIMEOUT: int = 120
    
    # Risk Management
    MIN_R_COEFFICIENT: float = 1.0
    MIN_PROFIT_MARGIN: float = 0.05
    RISK_PER_TRADE: float = 0.01
    MAX_PORTFOLIO_EXPOSURE: float = 0.90
    MAX_OPEN_POSITIONS: int = 10
    MAX_POSITION_SIZE: float = 0.20
    
    # Trading
    DEFAULT_TIF: str = "DAY"
    DEFAULT_ORDER_TYPE: str = "LMT"
    WORKFLOW_DELAY_SECONDS: int = 60
    
    # Chart
    CHART_WIDTH: int = 1920
    CHART_HEIGHT: int = 1080
    CHART_CACHE_TTL: int = 3600
    
    # Features
    AUTO_TRADING_ENABLED: bool = False
    PAPER_TRADING_MODE: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

