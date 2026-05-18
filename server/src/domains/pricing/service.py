"""Pricing domain — service and ingestion logic."""
import uuid
from datetime import datetime, timezone
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.domains.pricing.models import PriceRaw, PriceNormalized
from src.domains.cards.models import Card
from src.domains.markets.models import Market
from src.infrastructure.external_apis.ebay.client import EbayClient
from src.infrastructure.external_apis.fx.converter import fx_converter

logger = structlog.get_logger(__name__)


class PricingService:

    async def ingest_for_region(self, db: AsyncSession, region: str) -> int:
        await fx_converter.refresh_rates()
        market_result = await db.execute(
            select(Market).where(Market.region == region, Market.is_active == True)
        )
        market = market_result.scalar_one_or_none()
        if not market:
            logger.warning("No active market for region", region=region)
            return 0

        cards_result = await db.execute(select(Card))
        cards = list(cards_result.scalars().all())
        client = EbayClient(region=region)
        ingested = 0

        for card in cards:
            try:
                listings = await client.get_completed_listings(card.name, limit=15)
                now = datetime.now(timezone.utc)
                for listing in listings:
                    if listing.get("external_id"):
                        existing = await db.execute(
                            select(PriceRaw).where(PriceRaw.external_id == listing["external_id"])
                        )
                        if existing.scalar_one_or_none():
                            continue
                    raw = PriceRaw(
                        card_id=card.id,
                        market_id=market.id,
                        price=listing["price"],
                        currency=listing["currency"],
                        condition=listing.get("condition"),
                        sold_at=datetime.fromisoformat(listing["sold_at"].replace("Z", "+00:00"))
                        if listing.get("sold_at") else None,
                        fetched_at=now,
                        external_id=listing.get("external_id"),
                        title=listing.get("title"),
                        url=listing.get("url"),
                    )
                    db.add(raw)
                    await db.flush()
                    price_gbp = fx_converter.to_gbp(listing["price"], listing["currency"])
                    fx_rate = fx_converter.get_rate(listing["currency"])
                    norm = PriceNormalized(
                        price_raw_id=raw.id,
                        card_id=card.id,
                        market_id=market.id,
                        price_gbp=price_gbp,
                        condition_normalized=self._normalize_condition(listing.get("condition", "")),
                        fx_rate_used=fx_rate,
                        snapshot_at=raw.sold_at or now,
                    )
                    db.add(norm)
                    ingested += 1
            except Exception as e:
                logger.error("Ingestion failed", card=card.name, error=str(e))

        logger.info("Ingestion complete", region=region, records=ingested)
        return ingested

    def _normalize_condition(self, condition: str) -> str:
        c = condition.lower()
        if "psa 10" in c or "gem" in c: return "PSA10"
        if "psa 9" in c: return "PSA9"
        if "psa 8" in c: return "PSA8"
        if "bgs 9.5" in c: return "BGS9.5"
        if "bgs 9" in c: return "BGS9"
        if "near mint" in c or "nm" in c: return "NM"
        if "lightly played" in c or "lp" in c: return "LP"
        return "RAW"

    async def get_price_history(
        self, db: AsyncSession, card_id: uuid.UUID, market_id: uuid.UUID, limit: int = 30
    ) -> List[PriceNormalized]:
        result = await db.execute(
            select(PriceNormalized)
            .where(PriceNormalized.card_id == card_id, PriceNormalized.market_id == market_id)
            .order_by(desc(PriceNormalized.snapshot_at))
            .limit(limit)
        )
        return list(result.scalars().all())


pricing_service = PricingService()
