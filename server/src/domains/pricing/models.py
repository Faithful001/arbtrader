"""Pricing domain - ORM models for raw and normalized price records."""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class PriceRaw(Base, UUIDMixin, TimestampMixin):
    """Raw price record as fetched from the marketplace."""
    __tablename__ = "prices_raw"

    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)


class PriceNormalized(Base, UUIDMixin, TimestampMixin):
    """Normalized price snapshot - converted to GBP with standardized condition."""
    __tablename__ = "prices_normalized"

    price_raw_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prices_raw.id"), nullable=False)
    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False, index=True)
    price_gbp: Mapped[float] = mapped_column(Float, nullable=False)
    condition_normalized: Mapped[str] = mapped_column(String(50), nullable=False)  # RAW, PSA9, PSA10, BGS9, BGS9.5
    fx_rate_used: Mapped[float] = mapped_column(Float, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
