import asyncio
from sqlalchemy import select
from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.pricing.models import PriceNormalized
from src.domains.cards.models import Card
from src.domains.markets.models import Market
from src.domains.arbitrage.engine import PriceDataPoint, calculate_arbitrage

async def diagnose():
    async with AsyncSessionFactory() as db:
        # Find Mewtwo VSTAR
        card_res = await db.execute(select(Card).where(Card.name.like('%Mewtwo VSTAR%')))
        card = card_res.scalar_one_or_none()
        if not card:
            print("Card Mewtwo VSTAR not found!")
            return
        
        print(f"Diagnosing card: {card.name} ({card.id})")
        
        markets = list((await db.execute(select(Market).where(Market.is_active == True))).scalars())
        uk = next(m for m in markets if m.region == 'UK')
        us = next(m for m in markets if m.region == 'US')

        # Fetch UK prices
        uk_prices_res = await db.execute(
            select(PriceNormalized).where(
                PriceNormalized.card_id == card.id,
                PriceNormalized.market_id == uk.id,
                PriceNormalized.condition_normalized == 'RAW'
            )
        )
        uk_prices = list(uk_prices_res.scalars().all())

        # Fetch US prices
        us_prices_res = await db.execute(
            select(PriceNormalized).where(
                PriceNormalized.card_id == card.id,
                PriceNormalized.market_id == us.id,
                PriceNormalized.condition_normalized == 'RAW'
            )
        )
        us_prices = list(us_prices_res.scalars().all())

        print(f"Fetched {len(uk_prices)} UK prices, {len(us_prices)} US prices.")

        # Try US -> UK
        buy_dps = [
            PriceDataPoint(price_gbp=p.price_gbp, sold_at=p.snapshot_at, condition=p.condition_normalized, market_id=us.id)
            for p in us_prices
        ]
        sell_dps = [
            PriceDataPoint(price_gbp=p.price_gbp, sold_at=p.snapshot_at, condition=p.condition_normalized, market_id=uk.id)
            for p in uk_prices
        ]

        result = calculate_arbitrage(
            card_id=card.id,
            buy_market_id=us.id,
            sell_market_id=uk.id,
            buy_data_points=buy_dps,
            sell_data_points=sell_dps,
            buy_fee_percent=us.fee_percent,
            sell_fee_percent=uk.fee_percent,
            shipping_cost_gbp=uk.shipping_estimate_gbp,
            is_buy_uk=False,
            is_sell_uk=True
        )

        if not result:
            print("calculate_arbitrage returned None!")
        else:
            print(f"Result:")
            print(f"  Buy Price: {result.buy_price_gbp} GBP")
            print(f"  Sell Price: {result.sell_price_gbp} GBP")
            print(f"  Gross Spread: {result.gross_spread_gbp} GBP")
            print(f"  Net Profit: {result.net_profit_gbp} GBP")
            print(f"  ROI: {result.roi_percent}%")
            print(f"  Confidence: {result.confidence_score}")

if __name__ == '__main__':
    asyncio.run(diagnose())
