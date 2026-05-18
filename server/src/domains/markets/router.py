"""Markets domain — API router."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.domains.markets.service import market_service
from src.domains.markets.schemas import MarketResponse

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/", response_model=List[MarketResponse])
async def list_markets(db: AsyncSession = Depends(get_db)):
    return await market_service.list_markets(db)


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    market = await market_service.get_market(db, market_id)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return market


@router.post("/seed", status_code=201, tags=["dev"])
async def seed_markets(db: AsyncSession = Depends(get_db)):
    await market_service.seed_default_markets(db)
    return {"message": "Markets seeded (eBay UK, eBay US)"}
