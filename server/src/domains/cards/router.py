"""Cards domain — API router."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.domains.cards.service import card_service
from src.domains.cards.schemas import CardResponse, CardWithSetResponse, CardSetResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=List[CardWithSetResponse])
async def list_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await card_service.list_cards(db, skip=skip, limit=limit, search=search)


@router.get("/sets", response_model=List[CardSetResponse])
async def list_sets(db: AsyncSession = Depends(get_db)):
    return await card_service.list_sets(db)


@router.get("/{card_id}", response_model=CardWithSetResponse)
async def get_card(card_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    card = await card_service.get_card(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.post("/seed", status_code=201, tags=["dev"])
async def seed_cards(db: AsyncSession = Depends(get_db)):
    """Seed default Pokémon cards (dev only)."""
    await card_service.seed_default_cards(db)
    return {"message": "Cards seeded successfully"}
