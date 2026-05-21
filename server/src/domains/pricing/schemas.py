"""Pricing domain - Pydantic schemas."""
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


class ListingResponse(BaseModel):
    id: str
    card_name: str
    card_image_url: str | None = None
    rarity: str | None = None
    market: str
    region: str
    condition: str
    price_gbp: float
    listing_type: str | None = None
    ends_in: str | None = None
    url: str | None = None
    sold_count: int = 0
