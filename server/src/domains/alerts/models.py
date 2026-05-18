"""Alerts domain — ORM models."""
import uuid
from sqlalchemy import String, Boolean, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class Alert(Base, UUIDMixin, TimestampMixin):
    """Alert rule defined by a user."""
    __tablename__ = "alerts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # trigger_type: new_opportunity | price_drop | undervalued | auction_ending
    conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # conditions: {min_profit_gbp, min_roi_percent, card_id, market_id, ...}
    delivery_channel: Mapped[str] = mapped_column(String(20), default="telegram", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AlertTrigger(Base, UUIDMixin, TimestampMixin):
    """Log of a fired alert instance."""
    __tablename__ = "alert_triggers"

    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False, index=True)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
