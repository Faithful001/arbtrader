"""Automation domain — ORM models (future-safe stubs)."""
import uuid
from sqlalchemy import String, Boolean, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class AutomationRule(Base, UUIDMixin, TimestampMixin):
    """
    Automation rule — architecturally prepared, execution disabled at MVP.
    Stores rule definitions in DB; no hardcoded logic.
    """
    __tablename__ = "automation_rules"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # rule_type: auto_bid | roi_execute | price_alert_buy
    conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    actions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # NOTE: is_active is locked to False in MVP — no execution allowed
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
