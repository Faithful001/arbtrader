import asyncio
from sqlalchemy import select
from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.arbitrage.models import ArbitrageOpportunity
from src.domains.cards.models import Card

async def check_opportunities():
    async with AsyncSessionFactory() as db:
        query = select(ArbitrageOpportunity, Card).join(Card, Card.id == ArbitrageOpportunity.card_id)
        results = await db.execute(query)
        rows = results.all()
        print(f"Total opportunities in DB: {len(rows)}")
        for i, (opp, card) in enumerate(rows):
            print(f"{i+1}. Card: {card.name} ({card.number}) - Profit: {opp.net_profit_gbp} GBP - Conf: {opp.confidence_score}%")

if __name__ == "__main__":
    asyncio.run(check_opportunities())
