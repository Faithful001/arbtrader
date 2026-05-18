"""Arbitrage domain — API router."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.core.config import settings
from src.domains.arbitrage.service import arbitrage_service
from src.domains.arbitrage.schemas import OpportunityFeedResponse, OpportunityResponse, RecalcResponse

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.get("/feed", response_model=OpportunityFeedResponse)
async def get_opportunity_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_profit: Optional[float] = Query(None),
    min_confidence: Optional[float] = Query(None),
    sort_by: str = Query("net_profit_gbp", regex="^(net_profit_gbp|roi_percent|confidence_score)$"),
    db: AsyncSession = Depends(get_db),
):
    if settings.USE_MOCK_DATA:
        mock = await arbitrage_service.get_mock_feed()
        page_items = mock[skip: skip + limit]
        return OpportunityFeedResponse(
            items=page_items,
            total=len(mock),
            page=skip // limit + 1,
            page_size=limit,
        )

    items, total = await arbitrage_service.get_opportunities_feed(
        db,
        skip=skip,
        limit=limit,
        min_profit=min_profit,
        min_confidence=min_confidence,
        sort_by=sort_by,
    )
    return OpportunityFeedResponse(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    opp = await arbitrage_service.get_opportunity(db, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.post("/recalculate", response_model=RecalcResponse)
async def trigger_recalculate(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Manually trigger arbitrage recalculation (MVP: manual refresh)."""
    try:
        from src.domains.arbitrage.tasks import recalculate_all_opportunities
        task = recalculate_all_opportunities.delay()
        return RecalcResponse(triggered=True, task_id=task.id, message="Recalculation queued")
    except Exception:
        # If Celery not available, run synchronously
        count = await arbitrage_service.recalculate_all(db)
        return RecalcResponse(triggered=True, message=f"Recalculated synchronously: {count} opportunities")
