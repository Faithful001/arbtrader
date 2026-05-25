"""Cards domain - service layer."""
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
        """Seed Pokémon card sets dynamically by fetching from Pokémon TCG API."""
        import httpx
        from src.domains.cards.models import CardSet, Card

        # 1. Base Set
        existing_base = await db.execute(select(CardSet).where(CardSet.set_code == "BS"))
        base_set = existing_base.scalar_one_or_none()
        if not base_set:
            base_set = CardSet(
                name="Base Set",
                release_year=1999,
                total_cards=102,
                series="Original",
                set_code="BS",
            )
            db.add(base_set)
            await db.flush()

        # Fetch cards from Pokémon TCG API and upsert
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.pokemontcg.io/v2/cards?q=set.id:base1", timeout=15.0)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    target_names = {"Charizard", "Blastoise", "Venusaur", "Pikachu", "Mewtwo", "Raichu", "Gyarados", "Alakazam"}
                    seeded_count = 0
                    for card_data in data:
                        name = card_data.get("name")
                        if name in target_names:
                            rarity = card_data.get("rarity", "Common")
                            card_type = card_data.get("types", ["Colorless"])[0]
                            hp = int(card_data.get("hp", "0")) if card_data.get("hp") else 0
                            number = card_data.get("number")
                            img = card_data.get("images", {}).get("large")

                            # Check if card already exists in this set
                            card_query = await db.execute(
                                select(Card).where(Card.set_id == base_set.id, Card.name == name)
                            )
                            existing_card = card_query.scalar_one_or_none()
                            if existing_card:
                                # Update dynamic fields
                                existing_card.number = number
                                existing_card.rarity = rarity
                                existing_card.card_type = card_type
                                existing_card.hp = hp
                                existing_card.image_url = img
                            else:
                                db.add(Card(set_id=base_set.id, name=name, number=number,
                                            rarity=rarity, card_type=card_type, hp=hp, image_url=img))
                            seeded_count += 1
                    print(f"Dynamically seeded/updated {seeded_count} cards for Base Set.")
                else:
                    raise Exception(f"API returned status code {response.status_code}")
        except Exception as e:
            # Fallback to hardcoded if API is offline or rate limited
            print(f"Failed to fetch Base Set from API, using fallback: {e}")
            pokemon_cards = [
                ("Charizard", "4", "Rare Holo", "Fire", 120, "https://images.pokemontcg.io/base1/4_hires.png"),
                ("Blastoise", "2", "Rare Holo", "Water", 100, "https://images.pokemontcg.io/base1/2_hires.png"),
                ("Venusaur", "15", "Rare Holo", "Grass", 100, "https://images.pokemontcg.io/base1/15_hires.png"),
                ("Pikachu", "58", "Common", "Lightning", 40, "https://images.pokemontcg.io/base1/58_hires.png"),
                ("Mewtwo", "10", "Rare Holo", "Psychic", 60, "https://images.pokemontcg.io/base1/10_hires.png"),
                ("Raichu", "14", "Rare Holo", "Lightning", 80, "https://images.pokemontcg.io/base1/14_hires.png"),
                ("Gyarados", "6", "Rare Holo", "Water", 100, "https://images.pokemontcg.io/base1/6_hires.png"),
                ("Alakazam", "1", "Rare Holo", "Psychic", 80, "https://images.pokemontcg.io/base1/1_hires.png"),
            ]
            for name, number, rarity, card_type, hp, img in pokemon_cards:
                card_query = await db.execute(
                    select(Card).where(Card.set_id == base_set.id, Card.name == name)
                )
                existing_card = card_query.scalar_one_or_none()
                if existing_card:
                    existing_card.number = number
                    existing_card.rarity = rarity
                    existing_card.card_type = card_type
                    existing_card.hp = hp
                    existing_card.image_url = img
                else:
                    db.add(Card(set_id=base_set.id, name=name, number=number,
                                rarity=rarity, card_type=card_type, hp=hp, image_url=img))
        await db.flush()

        # 2. Crown Zenith
        existing_cz = await db.execute(select(CardSet).where(CardSet.set_code == "CRZ"))
        cz_set = existing_cz.scalar_one_or_none()
        if not cz_set:
            cz_set = CardSet(
                name="Crown Zenith",
                release_year=2023,
                total_cards=159,
                series="Sword & Shield",
                set_code="CRZ",
            )
            db.add(cz_set)
            await db.flush()

        # Fetch cards from Pokémon TCG API and upsert
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.pokemontcg.io/v2/cards?q=set.id:swsh12pt5", timeout=15.0)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    target_names = {"Giratina VSTAR", "Arceus VSTAR", "Origin Forme Dialga VSTAR", "Origin Forme Palkia VSTAR", "Mewtwo VSTAR", "Suicune V", "Pikachu", "Charizard VSTAR"}
                    seeded_count = 0
                    for card_data in data:
                        name = card_data.get("name")
                        if name in target_names:
                            rarity = card_data.get("rarity", "Ultra Rare")
                            card_type = card_data.get("types", ["Colorless"])[0]
                            hp = int(card_data.get("hp", "0")) if card_data.get("hp") else 0
                            number = card_data.get("number")
                            img = card_data.get("images", {}).get("large")

                            # Check if card already exists in this set
                            card_query = await db.execute(
                                select(Card).where(Card.set_id == cz_set.id, Card.name == name)
                            )
                            existing_card = card_query.scalar_one_or_none()
                            if existing_card:
                                # Update dynamic fields
                                existing_card.number = number
                                existing_card.rarity = rarity
                                existing_card.card_type = card_type
                                existing_card.hp = hp
                                existing_card.image_url = img
                            else:
                                db.add(Card(set_id=cz_set.id, name=name, number=number,
                                            rarity=rarity, card_type=card_type, hp=hp, image_url=img))
                            seeded_count += 1
                    print(f"Dynamically seeded/updated {seeded_count} cards for Crown Zenith.")
                else:
                    raise Exception(f"API returned status code {response.status_code}")
        except Exception as e:
            print(f"Failed to fetch Crown Zenith from API, using fallback: {e}")
            cz_cards = [
                ("Giratina VSTAR", "GG69", "Secret Rare", "Dragon", 280, "https://images.pokemontcg.io/swsh12pt5/gg69_hires.png"),
                ("Arceus VSTAR", "GG70", "Secret Rare", "Colorless", 280, "https://images.pokemontcg.io/swsh12pt5/gg70_hires.png"),
                ("Origin Forme Dialga VSTAR", "GG68", "Secret Rare", "Metal", 280, "https://images.pokemontcg.io/swsh12pt5/gg68_hires.png"),
                ("Origin Forme Palkia VSTAR", "GG67", "Secret Rare", "Water", 280, "https://images.pokemontcg.io/swsh12pt5/gg67_hires.png"),
                ("Mewtwo VSTAR", "GG44", "Ultra Rare", "Psychic", 260, "https://images.pokemontcg.io/swsh12pt5/gg44_hires.png"),
                ("Suicune V", "GG38", "Ultra Rare", "Water", 220, "https://images.pokemontcg.io/swsh12pt5/gg38_hires.png"),
                ("Pikachu", "160/159", "Secret Rare", "Lightning", 70, "https://images.pokemontcg.io/swsh12pt5/160_hires.png"),
                ("Charizard VSTAR", "019/159", "Ultra Rare", "Fire", 280, "https://images.pokemontcg.io/swsh12pt5/19_hires.png"),
            ]
            for name, number, rarity, card_type, hp, img in cz_cards:
                card_query = await db.execute(
                    select(Card).where(Card.set_id == cz_set.id, Card.name == name)
                )
                existing_card = card_query.scalar_one_or_none()
                if existing_card:
                    existing_card.number = number
                    existing_card.rarity = rarity
                    existing_card.card_type = card_type
                    existing_card.hp = hp
                    existing_card.image_url = img
                else:
                    db.add(Card(set_id=cz_set.id, name=name, number=number,
                                rarity=rarity, card_type=card_type, hp=hp, image_url=img))
        await db.flush()


card_service = CardService()
