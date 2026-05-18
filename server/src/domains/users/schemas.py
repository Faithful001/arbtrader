"""Users domain — Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator


class UserPreferences(BaseModel):
    min_profit_gbp: float = 5.0
    min_confidence: float = 0.6
    notify_telegram: bool = True
    notify_email: bool = False
    currency_display: str = "GBP"


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    telegram_chat_id: Optional[str]
    is_active: bool
    preferences: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
