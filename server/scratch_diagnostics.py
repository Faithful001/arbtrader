import asyncio
from sqlalchemy import select, func, desc
from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.pricing.models import PriceNormalized
from src.domains.cards.models import Card
from src.domains.markets.models import Market

async def run_diagnostics():
    async with AsyncSessionFactory() as db:
        markets = list((await db.execute(select(Market).where(Market.is_active == True))).scalars())
        uk = next(m for m in markets if m.region == 'UK')
        us = next(m for m in markets if m.region == 'US')

        # Get per-card avg price in each market, find spreads
        uk_avg = select(
            PriceNormalized.card_id,
            func.avg(PriceNormalized.price_gbp).label('uk_avg'),
            func.count().label('uk_n')
        ).where(PriceNormalized.market_id == uk.id, PriceNormalized.condition_normalized == 'RAW').group_by(PriceNormalized.card_id).subquery()

        us_avg = select(
            PriceNormalized.card_id,
            func.avg(PriceNormalized.price_gbp).label('us_avg'),
            func.count().label('us_n')
        ).where(PriceNormalized.market_id == us.id, PriceNormalized.condition_normalized == 'RAW').group_by(PriceNormalized.card_id).subquery()

        q = (
            select(Card.name, uk_avg.c.uk_avg, us_avg.c.us_avg, uk_avg.c.uk_n, us_avg.c.us_n)
            .join(uk_avg, Card.id == uk_avg.c.card_id)
            .join(us_avg, Card.id == us_avg.c.card_id)
            .order_by(desc(uk_avg.c.uk_avg - us_avg.c.us_avg))
            .limit(20)
        )
        rows = (await db.execute(q)).all()
        print('Top 20 cards by UK-US spread (raw avg prices):')
        print(f"{'Card':<40} {'UK avg':>8} {'US avg':>8} {'Spread':>8} {'UK n':>5} {'US n':>5}")
        for r in rows:
            spread = r.uk_avg - r.us_avg
            print(f"{r.name:<40} {r.uk_avg:>8.2f} {r.us_avg:>8.2f} {spread:>8.2f} {r.uk_n:>5} {r.us_n:>5}")

if __name__ == '__main__':
    asyncio.run(run_diagnostics())
