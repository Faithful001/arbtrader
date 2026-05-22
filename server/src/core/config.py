from functools import lru_cache
from typing import List, Union, Optional
import os

from pydantic import field_validator
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: str = os.getenv("APP_ENV")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY")
    APP_DEBUG: bool = os.getenv("APP_DEBUG")
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "https://arbtradr.vercel.app"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL")

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")

    GMAIL_USER: str = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD")

    # eBay
    EBAY_APP_ID: Optional[str] = os.getenv("EBAY_APP_ID")
    EBAY_DEV_ID: Optional[str] = os.getenv("EBAY_DEV_ID")
    EBAY_CERT_ID: Optional[str] = os.getenv("EBAY_CERT_ID")
    EBAY_CLIENT_ID: Optional[str] = os.getenv("EBAY_CLIENT_ID")
    EBAY_CLIENT_SECRET: Optional[str] = os.getenv("EBAY_CLIENT_SECRET")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")

    # FX
    FX_API_KEY: str = os.getenv("FX_API_KEY")
    FX_BASE_CURRENCY: str = os.getenv("FX_BASE_CURRENCY")

    # Arbitrage engine
    ARBITRAGE_MIN_NET_PROFIT_GBP: float = os.getenv("ARBITRAGE_MIN_NET_PROFIT_GBP")
    ARBITRAGE_MIN_CONFIDENCE_SCORE: float = os.getenv("ARBITRAGE_MIN_CONFIDENCE_SCORE")
    ARBITRAGE_RECALC_INTERVAL_MINUTES: int = os.getenv("ARBITRAGE_RECALC_INTERVAL_MINUTES")
    PRICE_INGESTION_INTERVAL_MINUTES: int = os.getenv("PRICE_INGESTION_INTERVAL_MINUTES")
    PRICING_DATA_RETENTION_DAYS: int = 90


    # JWT
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = os.getenv("JWT_EXPIRE_MINUTES")  # 7 days

    # Mock Mode
    USE_MOCK_DATA: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
