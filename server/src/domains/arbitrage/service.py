"""Arbitrage domain — service layer."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.domains.arbitrage.models import ArbitrageOpportunity
from src.domains.arbitrage.engine import (
    ArbitrageResult,
    PriceDataPoint,
    calculate_arbitrage,
)
from src.domains.cards.models import Card
from src.domains.markets.models import Market
from src.domains.pricing.models import PriceNormalized
from src.core.config import settings

logger = structlog.get_logger(__name__)


class ArbitrageService:

    async def get_opportunities_feed(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        min_profit: Optional[float] = None,
        min_confidence: Optional[float] = None,
        sort_by: str = "net_profit_gbp",
    ) -> tuple[List[ArbitrageOpportunity], int]:
        min_profit = min_profit or settings.ARBITRAGE_MIN_NET_PROFIT_GBP
        min_confidence = min_confidence or settings.ARBITRAGE_MIN_CONFIDENCE_SCORE

        q = (
            select(ArbitrageOpportunity)
            .where(
                ArbitrageOpportunity.status == "active",
                ArbitrageOpportunity.net_profit_gbp >= min_profit,
                ArbitrageOpportunity.confidence_score >= min_confidence,
            )
        )
        count_q = q.with_only_columns(ArbitrageOpportunity.id)

        sort_col = {
            "net_profit_gbp": ArbitrageOpportunity.net_profit_gbp,
            "roi_percent": ArbitrageOpportunity.roi_percent,
            "confidence_score": ArbitrageOpportunity.confidence_score,
        }.get(sort_by, ArbitrageOpportunity.net_profit_gbp)

        q = q.order_by(desc(sort_col)).offset(skip).limit(limit)
        result = await db.execute(q)
        items = list(result.scalars().all())

        count_result = await db.execute(count_q)
        total = len(count_result.all())

        return items, total

    async def get_opportunity(
        self, db: AsyncSession, opp_id: uuid.UUID
    ) -> Optional[ArbitrageOpportunity]:
        result = await db.execute(
            select(ArbitrageOpportunity).where(ArbitrageOpportunity.id == opp_id)
        )
        return result.scalar_one_or_none()

    async def persist_result(
        self, db: AsyncSession, result: ArbitrageResult
    ) -> ArbitrageOpportunity:
        # Expire any existing active opportunity for same card+market pair
        existing = await db.execute(
            select(ArbitrageOpportunity).where(
                ArbitrageOpportunity.card_id == result.card_id,
                ArbitrageOpportunity.buy_market_id == result.buy_market_id,
                ArbitrageOpportunity.sell_market_id == result.sell_market_id,
                ArbitrageOpportunity.status == "active",
            )
        )
        for opp in existing.scalars().all():
            opp.status = "expired"

        opp = ArbitrageOpportunity(
            card_id=result.card_id,
            buy_market_id=result.buy_market_id,
            sell_market_id=result.sell_market_id,
            buy_price_gbp=result.buy_price_gbp,
            sell_price_gbp=result.sell_price_gbp,
            gross_spread_gbp=result.gross_spread_gbp,
            platform_fees_gbp=result.platform_fees_gbp,
            shipping_cost_gbp=result.shipping_cost_gbp,
            import_duties_gbp=result.import_duties_gbp,
            net_profit_gbp=result.net_profit_gbp,
            roi_percent=result.roi_percent,
            confidence_score=result.confidence_score,
            volume_score=result.volume_score,
            data_points_used=result.data_points_used,
            status="active",
            expires_at=result.expires_at,
        )
        db.add(opp)
        await db.flush()
        return opp

    async def recalculate_all(self, db: AsyncSession) -> int:
        """Recalculate arbitrage for all cards using stored normalized prices."""
        cards_result = await db.execute(select(Card))
        cards = list(cards_result.scalars().all())

        markets_result = await db.execute(select(Market).where(Market.is_active == True))
        markets = {m.id: m for m in markets_result.scalars().all()}

        count = 0
        market_list = list(markets.values())
        if len(market_list) < 2:
            logger.warning("Not enough markets for arbitrage calculation")
            return 0

        for card in cards:
            for i, buy_market in enumerate(market_list):
                for sell_market in market_list:
                    if buy_market.id == sell_market.id:
                        continue

                    buy_prices = await db.execute(
                        select(PriceNormalized).where(
                            PriceNormalized.card_id == card.id,
                            PriceNormalized.market_id == buy_market.id,
                        ).order_by(desc(PriceNormalized.snapshot_at)).limit(10)
                    )
                    sell_prices = await db.execute(
                        select(PriceNormalized).where(
                            PriceNormalized.card_id == card.id,
                            PriceNormalized.market_id == sell_market.id,
                        ).order_by(desc(PriceNormalized.snapshot_at)).limit(10)
                    )

                    buy_dps = [
                        PriceDataPoint(
                            price_gbp=p.price_gbp,
                            sold_at=p.snapshot_at,
                            condition=p.condition_normalized,
                            market_id=buy_market.id,
                        )
                        for p in buy_prices.scalars().all()
                    ]
                    sell_dps = [
                        PriceDataPoint(
                            price_gbp=p.price_gbp,
                            sold_at=p.snapshot_at,
                            condition=p.condition_normalized,
                            market_id=sell_market.id,
                        )
                        for p in sell_prices.scalars().all()
                    ]

                    result = calculate_arbitrage(
                        card_id=card.id,
                        buy_market_id=buy_market.id,
                        sell_market_id=sell_market.id,
                        buy_data_points=buy_dps,
                        sell_data_points=sell_dps,
                        buy_fee_percent=buy_market.fee_percent,
                        sell_fee_percent=sell_market.fee_percent,
                        shipping_cost_gbp=sell_market.shipping_estimate_gbp,
                    )

                    if result and result.net_profit_gbp >= settings.ARBITRAGE_MIN_NET_PROFIT_GBP:
                        await self.persist_result(db, result)
                        count += 1

        logger.info("Arbitrage recalculation complete", opportunities=count)
        return count

    async def get_mock_feed(self) -> List[dict]:
        """Return mock opportunity data when DB is empty or mock mode is on."""
        import random
        cards = [
            ("Charizard Base Set Holo", "https://images.pokemontcg.io/base1/4_hires.png"),
            ("Blastoise Base Set Holo", "https://images.pokemontcg.io/base1/2_hires.png"),
            ("Venusaur Base Set Holo", "https://images.pokemontcg.io/base1/15_hires.png"),
            ("Mewtwo Base Set Holo", "https://images.pokemontcg.io/base1/10_hires.png"),
            ("Lugia Neo Genesis", "https://images.pokemontcg.io/neo1/9_hires.png"),
            ("Gyarados Base Set Holo", "https://images.pokemontcg.io/base1/6_hires.png"),
            ("Umbreon Gold Star", "https://images.pokemontcg.io/ex5/17_hires.png"),
            ("Rayquaza EX Deoxys Holo", "https://images.pokemontcg.io/ex7/107_hires.png"),
        ]
        results = []
        for i, (name, img) in enumerate(cards):
            buy = round(random.uniform(40, 120), 2)
            sell = round(buy * random.uniform(1.15, 1.60), 2)
            gross = round(sell - buy, 2)
            fees = round(sell * 0.129, 2)
            ship = round(random.uniform(3.5, 15.0), 2)
            net = round(gross - fees - ship, 2)
            roi = round((net / buy) * 100, 1)
            conf = round(random.uniform(0.62, 0.97), 2)
            results.append({
                "id": str(uuid.uuid4()),
                "card_id": str(uuid.uuid4()),
                "card_name": name,
                "card_image_url": img,
                "buy_market_name": "eBay US",
                "sell_market_name": "eBay UK",
                "buy_price_gbp": buy,
                "sell_price_gbp": sell,
                "gross_spread_gbp": gross,
                "platform_fees_gbp": fees,
                "shipping_cost_gbp": ship,
                "import_duties_gbp": 0.0,
                "net_profit_gbp": max(net, 5.0),
                "roi_percent": max(roi, 8.0),
                "confidence_score": conf,
                "volume_score": round(random.uniform(0.3, 1.0), 2),
                "data_points_used": random.randint(4, 18),
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": None,
            })
        results.sort(key=lambda x: x["net_profit_gbp"], reverse=True)
        return results


arbitrage_service = ArbitrageService()
