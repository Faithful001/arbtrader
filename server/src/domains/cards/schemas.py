"""Cards domain - Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CardSetResponse(BaseModel):
    id: uuid.UUID
    name: str
    release_year: Optional[int]
    total_cards: Optional[int]
    series: Optional[str]
    set_code: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    set_id: uuid.UUID
    name: str
    number: Optional[str] = None
    rarity: Optional[str] = None
    card_type: Optional[str] = None
    hp: Optional[int] = None
    image_url: Optional[str] = None


class CardResponse(BaseModel):
    id: uuid.UUID
    set_id: uuid.UUID
    name: str
    number: Optional[str]
    rarity: Optional[str]
    card_type: Optional[str]
    hp: Optional[int]
    image_url: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class CardWithSetResponse(CardResponse):
    card_set: Optional[CardSetResponse] = None


class SoldItemDetail(BaseModel):
    title: Optional[str] = None
    price: float
    currency: str
    price_gbp: float
    url: Optional[str] = None
    sold_at: Optional[datetime] = None


class CardExplorerItem(BaseModel):
    id: uuid.UUID
    name: str
    number: Optional[str] = None
    rarity: Optional[str] = None
    card_type: Optional[str] = None
    image_url: Optional[str] = None
    set_name: str
    
    uk_avg: Optional[float] = None
    us_avg: Optional[float] = None
    uk_last_3_avg: Optional[float] = None
    us_last_3_avg: Optional[float] = None
    
    uk_last_3: List[SoldItemDetail] = []
    us_last_3: List[SoldItemDetail] = []
    uk_search_url: str
    us_search_url: str

