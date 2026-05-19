"""Markets domain - service layer."""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domains.markets.models import Market
from src.domains.markets.schemas import MarketCreate


class MarketService:

    async def list_markets(self, db: AsyncSession, active_only: bool = True) -> List[Market]:
        q = select(Market).order_by(Market.region)
        if active_only:
            q = q.where(Market.is_active == True)
        result = await db.execute(q)
        return list(result.scalars().all())

    async def get_market(self, db: AsyncSession, market_id: uuid.UUID) -> Optional[Market]:
        result = await db.execute(select(Market).where(Market.id == market_id))
        return result.scalar_one_or_none()

    async def seed_default_markets(self, db: AsyncSession) -> None:
        existing = await db.execute(select(Market).limit(1))
        if existing.scalar_one_or_none():
            return
        markets = [
            Market(name="eBay UK", region="UK", currency="GBP",
                   fee_percent=12.9, shipping_estimate_gbp=3.50,
                   url="https://www.ebay.co.uk"),
            Market(name="eBay US", region="US", currency="USD",
                   fee_percent=13.25, shipping_estimate_gbp=12.0,
                   url="https://www.ebay.com"),
        ]
        for m in markets:
            db.add(m)
        await db.flush()


market_service = MarketService()
