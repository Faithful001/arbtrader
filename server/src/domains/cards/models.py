"""Cards domain - ORM models."""
import uuid
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.database.base import Base, UUIDMixin, TimestampMixin


class CardSet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "card_sets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    series: Mapped[str | None] = mapped_column(String(100), nullable=True)
    set_code: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)

    cards: Mapped[list["Card"]] = relationship("Card", back_populates="card_set")


class Card(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cards"

    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("card_sets.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rarity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tcg_player_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    card_set: Mapped["CardSet"] = relationship("CardSet", back_populates="cards")
