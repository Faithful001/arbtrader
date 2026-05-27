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
        from sqlalchemy import delete

        # 1. Clean up non-Crown Zenith card sets and cards to focus exclusively on CRZ
        non_cz_cards_stmt = select(Card).join(CardSet).where(CardSet.set_code != "CRZ")
        non_cz_cards = (await db.execute(non_cz_cards_stmt)).scalars().all()
        non_cz_card_ids = [c.id for c in non_cz_cards]

        if non_cz_card_ids:
            # Delete transactions, portfolio holdings, raw/normalized prices, and arbitrage opportunities for non-CZ cards
            from src.domains.portfolio.models import Portfolio, Transaction
            from src.domains.pricing.models import PriceRaw, PriceNormalized
            from src.domains.arbitrage.models import ArbitrageOpportunity
            
            await db.execute(delete(Transaction).where(Transaction.card_id.in_(non_cz_card_ids)))
            await db.execute(delete(Portfolio).where(Portfolio.card_id.in_(non_cz_card_ids)))
            await db.execute(delete(ArbitrageOpportunity).where(ArbitrageOpportunity.card_id.in_(non_cz_card_ids)))
            await db.execute(delete(PriceNormalized).where(PriceNormalized.card_id.in_(non_cz_card_ids)))
            await db.execute(delete(PriceRaw).where(PriceRaw.card_id.in_(non_cz_card_ids)))
            await db.execute(delete(Card).where(Card.id.in_(non_cz_card_ids)))
            
        await db.execute(delete(CardSet).where(CardSet.set_code != "CRZ"))
        await db.flush()

        # 2. Seed/Update Crown Zenith Set
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

        # Fetch ALL cards from Pokémon TCG API and upsert (pageSize=250 covers the whole set)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.pokemontcg.io/v2/cards?q=set.id:swsh12pt5&pageSize=250", timeout=15.0)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    seeded_count = 0
                    for card_data in data:
                        name = card_data.get("name")
                        rarity = card_data.get("rarity", "Ultra Rare")
                        card_type = card_data.get("types", ["Colorless"])[0]
                        hp = int(card_data.get("hp", "0")) if card_data.get("hp") else 0
                        number = card_data.get("number")
                        img = card_data.get("images", {}).get("large")

                        # Check if card already exists in this set by name and card number
                        card_query = await db.execute(
                            select(Card).where(
                                Card.set_id == cz_set.id,
                                Card.name == name,
                                Card.number == number
                            )
                        )
                        existing_card = card_query.scalar_one_or_none()
                        if existing_card:
                            # Update dynamic fields
                            existing_card.rarity = rarity
                            existing_card.card_type = card_type
                            existing_card.hp = hp
                            existing_card.image_url = img
                        else:
                            db.add(Card(set_id=cz_set.id, name=name, number=number,
                                        rarity=rarity, card_type=card_type, hp=hp, image_url=img))
                        seeded_count += 1
                    print(f"Dynamically seeded/updated {seeded_count} cards for Crown Zenith via Pokemon TCG API.")
                else:
                    raise Exception(f"API returned status code {response.status_code}")
        except Exception as e:
            print(f"Failed to fetch Crown Zenith from Pokemon TCG API ({e}). Trying TCGdex API...")
            try:
                import asyncio
                async with httpx.AsyncClient() as client:
                    tcgdex_response = await client.get("https://api.tcgdex.net/v2/en/sets/swsh12.5", timeout=15.0)
                    if tcgdex_response.status_code == 200:
                        tcgdex_data = tcgdex_response.json()
                        cards_summary = tcgdex_data.get("cards", [])
                        
                        # Fetch details of all cards in parallel
                        async def fetch_tcgdex_card_details(c_id):
                            try:
                                c_resp = await client.get(f"https://api.tcgdex.net/v2/en/cards/{c_id}", timeout=10.0)
                                if c_resp.status_code == 200:
                                    return c_resp.json()
                            except Exception:
                                pass
                            return None
                        
                        tasks = [fetch_tcgdex_card_details(c.get("id")) for c in cards_summary if c.get("id")]
                        details_list = await asyncio.gather(*tasks)
                        
                        seeded_count = 0
                        for detail in details_list:
                            if not detail:
                                continue
                            name = detail.get("name")
                            rarity = detail.get("rarity", "Ultra Rare")
                            card_types = detail.get("types", ["Colorless"])
                            card_type = card_types[0] if card_types else "Colorless"
                            hp = int(detail.get("hp", "0")) if detail.get("hp") else 0
                            number = detail.get("localId")
                            img = f"{detail.get('image')}/high.png" if detail.get("image") else None
                            
                            card_query = await db.execute(
                                select(Card).where(
                                    Card.set_id == cz_set.id,
                                    Card.name == name,
                                    Card.number == number
                                )
                            )
                            existing_card = card_query.scalar_one_or_none()
                            if existing_card:
                                existing_card.rarity = rarity
                                existing_card.card_type = card_type
                                existing_card.hp = hp
                                existing_card.image_url = img
                            else:
                                db.add(Card(set_id=cz_set.id, name=name, number=number,
                                            rarity=rarity, card_type=card_type, hp=hp, image_url=img))
                            seeded_count += 1
                        print(f"Dynamically seeded/updated {seeded_count} cards for Crown Zenith via TCGdex API.")
                    else:
                        raise Exception(f"TCGdex returned status code {tcgdex_response.status_code}")
            except Exception as tcg_err:
                print(f"Failed to fetch from TCGdex API ({tcg_err}). Falling back to hardcoded core list...")
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
                        select(Card).where(
                            Card.set_id == cz_set.id,
                            Card.name == name,
                            Card.number == number
                        )
                    )
                    existing_card = card_query.scalar_one_or_none()
                    if existing_card:
                        existing_card.rarity = rarity
                        existing_card.card_type = card_type
                        existing_card.hp = hp
                        existing_card.image_url = img
                    else:
                        db.add(Card(set_id=cz_set.id, name=name, number=number,
                                    rarity=rarity, card_type=card_type, hp=hp, image_url=img))
        await db.flush()


card_service = CardService()
