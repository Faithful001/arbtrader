"""Alerts domain — Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AlertCreate(BaseModel):
    name: str
    trigger_type: str  # new_opportunity | price_drop | undervalued | auction_ending
    conditions: Dict[str, Any] = {}
    delivery_channel: str = "telegram"


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    trigger_type: str
    conditions: Dict[str, Any]
    delivery_channel: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class AlertTriggerResponse(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    payload: Dict[str, Any]
    delivered: bool
    delivery_error: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
