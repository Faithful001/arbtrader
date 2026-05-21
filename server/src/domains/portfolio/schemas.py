"""Portfolio domain - Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    card_id: uuid.UUID
    market_id: uuid.UUID
    quantity: int = 1
    buy_price_gbp: float
    buy_date: datetime
    condition: Optional[str] = None
    notes: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    card_id: uuid.UUID
    market_id: uuid.UUID
    quantity: int
    buy_price_gbp: float
    buy_date: datetime
    current_value_gbp: Optional[float]
    condition: Optional[str]
    notes: Optional[str]
    created_at: datetime
    # Computed fields joined from card
    card_name: Optional[str] = None
    card_image_url: Optional[str] = None
    unrealized_pnl_gbp: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    card_id: uuid.UUID
    market_id: uuid.UUID
    portfolio_id: Optional[uuid.UUID] = None
    transaction_type: str  # buy | sell
    quantity: int = 1
    price_gbp: float
    fees_gbp: float = 0.0
    transaction_date: datetime
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    card_id: uuid.UUID
    market_id: uuid.UUID
    transaction_type: str
    quantity: int
    price_gbp: float
    fees_gbp: float
    transaction_date: datetime
    notes: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class PnLHistoryPoint(BaseModel):
    date: str
    value: float


class PnLSummary(BaseModel):
    total_invested_gbp: float
    current_value_gbp: float
    total_realized_pnl_gbp: float
    total_unrealized_pnl_gbp: float
    total_pnl_gbp: float
    roi_percent: float
    holdings_count: int
    history: List[PnLHistoryPoint] = []
