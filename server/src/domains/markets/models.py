"""Markets domain - ORM models."""
from sqlalchemy import String, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class Market(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "markets"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # UK, US, JP
    currency: Mapped[str] = mapped_column(String(10), nullable=False)            # GBP, USD, JPY
    fee_percent: Mapped[float] = mapped_column(Float, default=12.9, nullable=False)
    shipping_estimate_gbp: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
