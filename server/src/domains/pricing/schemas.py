"""Pricing domain — Pydantic schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class PriceNormalizedResponse(BaseModel):
    id: uuid.UUID
    card_id: uuid.UUID
    market_id: uuid.UUID
    price_gbp: float
    condition_normalized: str
    fx_rate_used: float
    snapshot_at: datetime
    model_config = {"from_attributes": True}
