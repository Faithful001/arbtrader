"""Cards domain — Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional
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
