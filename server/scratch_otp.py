import asyncio
import os
import sys

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.domains.arbitrage.service import arbitrage_service
from src.domains.arbitrage.models import ArbitrageOpportunity
from src.domains.cards.models import Card
from src.infrastructure.database.session import AsyncSessionFactory
from sqlalchemy import select

async def main():
    async with AsyncSessionFactory() as session:
        print("RECALCULATING ARBITRAGE OPPORTUNITIES WITH OUTLIER FILTER...")
        opps_count = await arbitrage_service.recalculate_all(session)
        print(f"Recalculated {opps_count} opportunities.")
        await session.commit()
        
    print("\nNEW DYNAMIC ACTIVE OPPORTUNITIES:")
    async with AsyncSessionFactory() as session:
        opps_res = await session.execute(
            select(ArbitrageOpportunity).where(ArbitrageOpportunity.status == "active")
        )
        opps = opps_res.scalars().all()
        for o in opps:
            card_res = await session.execute(select(Card).where(Card.id == o.card_id))
            card = card_res.scalar_one_or_none()
            print(f"- {card.name if card else 'Unknown'}: Buy Ask £{o.buy_price_gbp:.2f}, Sell Bid £{o.sell_price_gbp:.2f}, Profit £{o.net_profit_gbp:.2f}, ROI {o.roi_percent:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
