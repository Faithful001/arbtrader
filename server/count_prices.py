import asyncio
from sqlalchemy import select, func
from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.pricing.models import PriceRaw, PriceNormalized
from src.domains.arbitrage.models import ArbitrageOpportunity
from src.domains.cards.models import Card

async def count_rows():
    async with AsyncSessionFactory() as db:
        cards_cnt = (await db.execute(select(func.count()).select_from(Card))).scalar()
        raw_cnt = (await db.execute(select(func.count()).select_from(PriceRaw))).scalar()
        norm_cnt = (await db.execute(select(func.count()).select_from(PriceNormalized))).scalar()
        arb_cnt = (await db.execute(select(func.count()).select_from(ArbitrageOpportunity))).scalar()
        print(f"Total Cards: {cards_cnt}")
        print(f"Total Raw Prices: {raw_cnt}")
        print(f"Total Normalized Prices: {norm_cnt}")
        print(f"Total Arbitrage Opportunities: {arb_cnt}")

if __name__ == "__main__":
    asyncio.run(count_rows())
