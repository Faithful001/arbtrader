"""Cards domain — service layer."""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.domains.cards.models import Card, CardSet


class CardService:

    async def list_cards(
        self, db: AsyncSession, skip: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> List[Card]:
        q = select(Card).options(selectinload(Card.card_set)).offset(skip).limit(limit)
        if search:
            q = q.where(Card.name.ilike(f"%{search}%"))
        result = await db.execute(q)
        return list(result.scalars().all())

    async def get_card(self, db: AsyncSession, card_id: uuid.UUID) -> Optional[Card]:
        result = await db.execute(
            select(Card).options(selectinload(Card.card_set)).where(Card.id == card_id)
        )
        return result.scalar_one_or_none()

    async def list_sets(self, db: AsyncSession) -> List[CardSet]:
        result = await db.execute(select(CardSet).order_by(CardSet.name))
        return list(result.scalars().all())

    async def seed_default_cards(self, db: AsyncSession) -> None:
        """Seed a base set of Pokémon cards for development."""
        from datetime import datetime, timezone
        existing = await db.execute(select(CardSet).limit(1))
        if existing.scalar_one_or_none():
            return

        base_set = CardSet(
            name="Base Set",
            release_year=1999,
            total_cards=102,
            series="Original",
            set_code="BS",
        )
        db.add(base_set)
        await db.flush()

        pokemon_cards = [
            ("Charizard", "4/102", "Holo Rare", "Fire", 120),
            ("Blastoise", "2/102", "Holo Rare", "Water", 100),
            ("Venusaur", "15/102", "Holo Rare", "Grass", 100),
            ("Pikachu", "58/102", "Common", "Lightning", 40),
            ("Mewtwo", "10/102", "Holo Rare", "Psychic", 60),
            ("Raichu", "14/102", "Holo Rare", "Lightning", 80),
            ("Gyarados", "6/102", "Holo Rare", "Water", 100),
            ("Alakazam", "1/102", "Holo Rare", "Psychic", 80),
        ]
        for name, number, rarity, card_type, hp in pokemon_cards:
            db.add(Card(set_id=base_set.id, name=name, number=number,
                        rarity=rarity, card_type=card_type, hp=hp))
        await db.flush()


card_service = CardService()
