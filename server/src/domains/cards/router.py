"""Cards domain - API router."""
import uuid
import urllib.parse
from collections import defaultdict
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.database.session import get_db
from src.domains.cards.service import card_service
from src.domains.cards.schemas import CardResponse, CardWithSetResponse, CardSetResponse, CardExplorerItem, SoldItemDetail
from src.domains.markets.models import Market
from src.domains.cards.models import Card, CardSet
from src.domains.pricing.models import PriceNormalized, PriceRaw

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/explorer", response_model=List[CardExplorerItem])
async def get_cards_explorer(
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch CZ Set
    cz_set_res = await db.execute(select(CardSet).where(CardSet.set_code == "CRZ"))
    cz_set = cz_set_res.scalar_one_or_none()
    if not cz_set:
        return []

    # 2. Fetch all markets
    markets_res = await db.execute(select(Market).where(Market.is_active == True))
    markets = list(markets_res.scalars().all())
    uk_market = next((m for m in markets if m.region == "UK"), None)
    us_market = next((m for m in markets if m.region == "US"), None)
    uk_id = uk_market.id if uk_market else None
    us_id = us_market.id if us_market else None

    # 3. Fetch all cards in Crown Zenith set
    cards_q = select(Card).where(Card.set_id == cz_set.id)
    if search:
        cards_q = cards_q.where(Card.name.ilike(f"%{search}%"))
    cards_res = await db.execute(cards_q)
    cards = list(cards_res.scalars().all())

    # 4. Fetch all normalized prices and raw prices
    prices_q = (
        select(PriceNormalized, PriceRaw)
        .join(PriceRaw, PriceNormalized.price_raw_id == PriceRaw.id)
        .where(PriceNormalized.condition_normalized == "RAW")
        .order_by(PriceRaw.sold_at.desc())
    )
    prices_res = await db.execute(prices_q)
    prices = list(prices_res.all())

    # 5. Group prices in Python
    uk_prices_by_card = defaultdict(list)
    us_prices_by_card = defaultdict(list)
    for pn, pr in prices:
        if pn.market_id == uk_id:
            uk_prices_by_card[pn.card_id].append((pn, pr))
        elif pn.market_id == us_id:
            us_prices_by_card[pn.card_id].append((pn, pr))

    # 6. Build response objects
    items = []
    for card in cards:
        # UK metrics
        uk_list = uk_prices_by_card[card.id]
        uk_avg = sum(p[0].price_gbp for p in uk_list) / len(uk_list) if uk_list else None
        
        uk_last_3_items = uk_list[:3]
        uk_last_3_avg = sum(p[0].price_gbp for p in uk_last_3_items) / len(uk_last_3_items) if uk_last_3_items else None
        uk_last_3_details = [
            SoldItemDetail(
                title=p[1].title,
                price=p[1].price,
                currency=p[1].currency,
                price_gbp=p[0].price_gbp,
                url=p[1].url,
                sold_at=p[1].sold_at,
            )
            for p in uk_last_3_items
        ]

        # US metrics
        us_list = us_prices_by_card[card.id]
        us_avg = sum(p[0].price_gbp for p in us_list) / len(us_list) if us_list else None
        
        us_last_3_items = us_list[:3]
        us_last_3_avg = sum(p[0].price_gbp for p in us_last_3_items) / len(us_last_3_items) if us_last_3_items else None
        us_last_3_details = [
            SoldItemDetail(
                title=p[1].title,
                price=p[1].price,
                currency=p[1].currency,
                price_gbp=p[0].price_gbp,
                url=p[1].url,
                sold_at=p[1].sold_at,
            )
            for p in us_last_3_items
        ]

        # Search terms
        search_query = f"{card.name} {card.number or ''}".strip()
        uk_search_url = f"https://www.ebay.co.uk/sch/i.html?_nkw={urllib.parse.quote(search_query)}"
        us_search_url = f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(search_query)}"

        items.append(
            CardExplorerItem(
                id=card.id,
                name=card.name,
                number=card.number,
                rarity=card.rarity,
                card_type=card.card_type,
                image_url=card.image_url,
                set_name=cz_set.name,
                uk_avg=uk_avg,
                us_avg=us_avg,
                uk_last_3_avg=uk_last_3_avg,
                us_last_3_avg=us_last_3_avg,
                uk_last_3=uk_last_3_details,
                us_last_3=us_last_3_details,
                uk_search_url=uk_search_url,
                us_search_url=us_search_url,
            )
        )

    # Sort cards by number / name to ensure a stable, neat presentation
    items.sort(key=lambda x: (x.number or "", x.name))
    return items


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

