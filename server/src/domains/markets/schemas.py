"""Markets domain — Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MarketCreate(BaseModel):
    name: str
    region: str
    currency: str
    fee_percent: float = 12.9
    shipping_estimate_gbp: float = 5.0
    url: Optional[str] = None
    notes: Optional[str] = None


class MarketResponse(BaseModel):
    id: uuid.UUID
    name: str
    region: str
    currency: str
    fee_percent: float
    shipping_estimate_gbp: float
    url: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
