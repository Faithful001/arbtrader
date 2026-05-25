"""Pricing domain - API router."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.domains.pricing.service import pricing_service
from src.domains.pricing.schemas import PriceNormalizedResponse, ListingResponse

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/history/{card_id}/{market_id}", response_model=List[PriceNormalizedResponse])
async def get_price_history(
    card_id: uuid.UUID,
    market_id: uuid.UUID,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await pricing_service.get_price_history(db, card_id, market_id, limit)


@router.get("/variations/{card_id}")
async def get_card_variations(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await pricing_service.get_dynamic_variations(db, card_id)


@router.get("/listings", response_model=List[ListingResponse])
async def get_recent_listings(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    return await pricing_service.get_recent_listings(db, limit)


@router.post("/ingest/{region}", tags=["dev"])
async def trigger_ingest(region: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger price ingestion for a region (dev/manual)."""
    try:
        from src.domains.pricing.tasks import ingest_ebay_prices
        task = ingest_ebay_prices.delay(region)
        return {"triggered": True, "task_id": task.id, "region": region}
    except Exception:
        count = await pricing_service.ingest_for_region(db, region)
        await db.commit()
        return {"triggered": True, "region": region, "records": count}
