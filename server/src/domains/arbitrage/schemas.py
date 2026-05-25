"""Arbitrage domain - Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OpportunityResponse(BaseModel):
    id: uuid.UUID
    card_id: uuid.UUID
    card_name: Optional[str] = None
    card_image_url: Optional[str] = None
    card_rarity: Optional[str] = None
    buy_market_id: uuid.UUID
    sell_market_id: uuid.UUID
    buy_market_name: Optional[str] = None
    sell_market_name: Optional[str] = None
    buy_price_gbp: float
    sell_price_gbp: float
    gross_spread_gbp: float
    platform_fees_gbp: float
    shipping_cost_gbp: float
    import_duties_gbp: float
    net_profit_gbp: float
    roi_percent: float
    confidence_score: float
    volume_score: float
    data_points_used: Optional[int]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    model_config = {"from_attributes": True}


class OpportunityFeedResponse(BaseModel):
    items: List[OpportunityResponse]
    total: int
    page: int
    page_size: int


class RecalcResponse(BaseModel):
    triggered: bool
    task_id: Optional[str] = None
    message: str
