"""
Debug: run ingestion for the first 5 unpriced cards, print eBay results.
ASCII-safe output to avoid Windows codec issues.
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.cards.models import Card
from src.domains.pricing.models import PriceRaw
from src.domains.pricing.service import pricing_service
from src.infrastructure.external_apis.ebay.client import EbayClient

async def main():
    async with AsyncSessionFactory() as db:
        priced_ids = select(PriceRaw.card_id).distinct()
        result = await db.execute(
            select(Card)
            .options(selectinload(Card.card_set))
            .where(Card.id.not_in(priced_ids))
            .limit(5)
        )
        cards = list(result.scalars().all())
        print(f"Sampling {len(cards)} unpriced cards...\n")

        client = EbayClient(region="US")
        token = await client._get_app_token()
        print(f"eBay token available: {bool(token)}\n")

        for card in cards:
            set_name = card.card_set.name if card.card_set else ""
            query = f"{card.name} {set_name} {card.number or ''}".strip()
            print(f"--- Card: {card.name} | number in DB: '{card.number}' ---")
            print(f"    Query sent to eBay: '{query}'")
            try:
                listings = await client.get_completed_listings(query, limit=5)
                print(f"    Listings returned: {len(listings)}")
                for lst in listings:
                    title = lst.get("title", "")
                    matched = pricing_service.is_genuine_listing_match(card, title)
                    status = "PASS" if matched else "FAIL"
                    print(f"      [{status}] [{lst.get('price')} {lst.get('currency')}] {title[:75]}")
            except Exception as e:
                print(f"    ERROR: {e}")
            print()

asyncio.run(main())
