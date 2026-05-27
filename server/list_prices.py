import asyncio
from sqlalchemy import select, func
from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.pricing.models import PriceRaw
from src.domains.cards.models import Card

async def check_prices():
    async with AsyncSessionFactory() as db:
        query = select(Card.name, func.count(PriceRaw.id)).join(PriceRaw, PriceRaw.card_id == Card.id).group_by(Card.name)
        results = await db.execute(query)
        rows = results.all()
        print(f"Cards with prices in DB:")
        for name, count in rows:
            print(f"- {name}: {count} price records")

if __name__ == "__main__":
    asyncio.run(check_prices())
