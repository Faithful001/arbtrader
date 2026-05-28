"""Arbitrage domain - service layer."""
from sqlalchemy import func
from src.domains.arbitrage.schemas import OpportunityResponse
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
        rarity: Optional[str] = None,
    ) -> tuple[List[OpportunityResponse], int]:
        min_profit = min_profit or settings.ARBITRAGE_MIN_NET_PROFIT_GBP
        min_confidence = min_confidence or settings.ARBITRAGE_MIN_CONFIDENCE_SCORE

        q = (
            select(ArbitrageOpportunity)
            .join(Card, ArbitrageOpportunity.card_id == Card.id)
            .join(Market, ArbitrageOpportunity.buy_market_id == Market.id)
            .where(
                ArbitrageOpportunity.status == "active",
                ArbitrageOpportunity.net_profit_gbp >= min_profit,
                ArbitrageOpportunity.confidence_score >= min_confidence,
            )
        )

        # Rarity filter
        if rarity:
            q = q.where(Card.rarity == rarity)

        sort_col = {
            "net_profit_gbp": ArbitrageOpportunity.net_profit_gbp,
            "roi_percent": ArbitrageOpportunity.roi_percent,
            "confidence_score": ArbitrageOpportunity.confidence_score,
        }.get(sort_by, ArbitrageOpportunity.net_profit_gbp)

        count_q = select(func.count()).select_from(q.subquery())
        q = q.order_by(desc(sort_col)).offset(skip).limit(limit)

        result = await db.execute(q)
        opportunities = list(result.scalars().all())

        count_result = await db.execute(count_q)
        total = count_result.scalar() or 0

        # Fetch sell markets separately since we can only join one market above
        sell_market_ids = {o.sell_market_id for o in opportunities}
        buy_market_ids = {o.buy_market_id for o in opportunities}
        card_ids = {o.card_id for o in opportunities}

        markets_result = await db.execute(
            select(Market).where(Market.id.in_(sell_market_ids | buy_market_ids))
        )
        markets = {m.id: m for m in markets_result.scalars().all()}

        cards_result = await db.execute(
            select(Card).where(Card.id.in_(card_ids))
        )
        cards = {c.id: c for c in cards_result.scalars().all()}

        # Build enriched response objects
        items = []
        for opp in opportunities:
            card = cards.get(opp.card_id)
            buy_market = markets.get(opp.buy_market_id)
            sell_market = markets.get(opp.sell_market_id)

            items.append(OpportunityResponse(
                id=opp.id,
                card_id=opp.card_id,
                card_name=card.name if card else None,
                card_image_url=card.image_url if card else None,
                card_rarity=card.rarity if card else None,
                card_number=card.number if card else None,
                buy_market_id=opp.buy_market_id,
                sell_market_id=opp.sell_market_id,
                buy_market_name=buy_market.name if buy_market else None,
                sell_market_name=sell_market.name if sell_market else None,
                buy_price_gbp=opp.buy_price_gbp,
                sell_price_gbp=opp.sell_price_gbp,
                gross_spread_gbp=opp.gross_spread_gbp,
                platform_fees_gbp=opp.platform_fees_gbp,
                shipping_cost_gbp=opp.shipping_cost_gbp,
                import_duties_gbp=opp.import_duties_gbp,
                net_profit_gbp=opp.net_profit_gbp,
                roi_percent=opp.roi_percent,
                confidence_score=opp.confidence_score,
                volume_score=opp.volume_score,
                data_points_used=opp.data_points_used,
                status=opp.status,
                created_at=opp.created_at,
                expires_at=opp.expires_at,
            ))

        return items, total

    async def get_opportunity(
        self, db: AsyncSession, opp_id: uuid.UUID
    ) -> Optional[ArbitrageOpportunity]:
        result = await db.execute(
            select(ArbitrageOpportunity).where(ArbitrageOpportunity.id == opp_id)
        )
        return result.scalar_one_or_none()

    async def get_opportunity_by_card_id(
        self, db: AsyncSession, card_id: uuid.UUID
    ) -> Optional[OpportunityResponse]:
        """Fetch active arbitrage opportunity for a card, if one exists."""
        q = (
            select(ArbitrageOpportunity)
            .where(
                ArbitrageOpportunity.card_id == card_id,
                ArbitrageOpportunity.status == "active",
            )
            .order_by(desc(ArbitrageOpportunity.created_at))
            .limit(1)
        )
        result = await db.execute(q)
        opp = result.scalar_one_or_none()
        if not opp:
            return None

        # Fetch markets and cards to build OpportunityResponse
        markets_result = await db.execute(
            select(Market).where(Market.id.in_([opp.buy_market_id, opp.sell_market_id]))
        )
        markets = {m.id: m for m in markets_result.scalars().all()}
        card_result = await db.execute(
            select(Card).where(Card.id == card_id)
        )
        card = card_result.scalar_one_or_none()

        buy_market = markets.get(opp.buy_market_id)
        sell_market = markets.get(opp.sell_market_id)

        return OpportunityResponse(
            id=opp.id,
            card_id=opp.card_id,
            card_name=card.name if card else None,
            card_image_url=card.image_url if card else None,
            card_rarity=card.rarity if card else None,
            card_number=card.number if card else None,
            buy_market_id=opp.buy_market_id,
            sell_market_id=opp.sell_market_id,
            buy_market_name=buy_market.name if buy_market else None,
            sell_market_name=sell_market.name if sell_market else None,
            buy_price_gbp=opp.buy_price_gbp,
            sell_price_gbp=opp.sell_price_gbp,
            gross_spread_gbp=opp.gross_spread_gbp,
            platform_fees_gbp=opp.platform_fees_gbp,
            shipping_cost_gbp=opp.shipping_cost_gbp,
            import_duties_gbp=opp.import_duties_gbp,
            net_profit_gbp=opp.net_profit_gbp,
            roi_percent=opp.roi_percent,
            confidence_score=opp.confidence_score,
            volume_score=opp.volume_score,
            data_points_used=opp.data_points_used,
            status=opp.status,
            created_at=opp.created_at,
            expires_at=opp.expires_at,
        )

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
                            PriceNormalized.condition_normalized == "RAW",
                        ).order_by(desc(PriceNormalized.snapshot_at)).limit(100)
                    )
                    sell_prices = await db.execute(
                        select(PriceNormalized).where(
                            PriceNormalized.card_id == card.id,
                            PriceNormalized.market_id == sell_market.id,
                            PriceNormalized.condition_normalized == "RAW",
                        ).order_by(desc(PriceNormalized.snapshot_at)).limit(100)
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
                        is_buy_uk=(buy_market.region == "UK"),
                        is_sell_uk=(sell_market.region == "UK"),
                    )

                    if result and result.net_profit_gbp >= settings.ARBITRAGE_MIN_NET_PROFIT_GBP:
                        await self.persist_result(db, result)
                        count += 1

        logger.info("Arbitrage recalculation complete", opportunities=count)
        return count


arbitrage_service = ArbitrageService()
