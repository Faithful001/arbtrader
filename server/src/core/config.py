"""
Core configuration — loaded from environment variables via Pydantic Settings.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev-secret-key-change-in-production"
    APP_DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/arbtrader"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # eBay
    EBAY_APP_ID: str = "mock-app-id"
    EBAY_DEV_ID: str = "mock-dev-id"
    EBAY_CERT_ID: str = "mock-cert-id"
    EBAY_CLIENT_ID: str = "mock-client-id"
    EBAY_CLIENT_SECRET: str = "mock-client-secret"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = "mock-telegram-token"

    # FX
    FX_API_KEY: str = "mock-fx-key"
    FX_BASE_CURRENCY: str = "GBP"

    # Arbitrage engine
    ARBITRAGE_MIN_NET_PROFIT_GBP: float = 5.0
    ARBITRAGE_MIN_CONFIDENCE_SCORE: float = 0.6
    ARBITRAGE_RECALC_INTERVAL_MINUTES: int = 60
    PRICE_INGESTION_INTERVAL_MINUTES: int = 120

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # Mock Mode
    USE_MOCK_DATA: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
