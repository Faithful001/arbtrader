"""Arbitrage domain - ORM models for opportunities."""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class ArbitrageOpportunity(Base, UUIDMixin, TimestampMixin):
    """A calculated arbitrage opportunity between two markets for a card."""
    __tablename__ = "arbitrage_opportunities"

    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    buy_market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    sell_market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)

    # Prices (all GBP)
    buy_price_gbp: Mapped[float] = mapped_column(Float, nullable=False)
    sell_price_gbp: Mapped[float] = mapped_column(Float, nullable=False)

    # Costs & profit
    gross_spread_gbp: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fees_gbp: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_cost_gbp: Mapped[float] = mapped_column(Float, nullable=False)
    import_duties_gbp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_profit_gbp: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    roi_percent: Mapped[float] = mapped_column(Float, nullable=False)

    # Scoring
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0–1.0
    volume_score: Mapped[float] = mapped_column(Float, nullable=False)       # sales count
    data_points_used: Mapped[int | None] = mapped_column(nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    # status: active | expired | executed
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
