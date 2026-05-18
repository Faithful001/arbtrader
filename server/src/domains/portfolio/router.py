"""Portfolio domain — API router."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.core.security import get_current_user_id
from src.domains.portfolio.service import portfolio_service
from src.domains.portfolio.schemas import (
    PortfolioCreate, PortfolioResponse,
    TransactionCreate, TransactionResponse,
    PnLSummary,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/", response_model=List[PortfolioResponse])
async def list_holdings(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    return await portfolio_service.list_holdings(db, uuid.UUID(user_id))


@router.post("/", response_model=PortfolioResponse, status_code=201)
async def add_holding(
    data: PortfolioCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.add_holding(db, uuid.UUID(user_id), data)


@router.delete("/{holding_id}", status_code=204)
async def remove_holding(
    holding_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    holding = await portfolio_service.get_holding(db, holding_id)
    if not holding or str(holding.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Holding not found")
    await portfolio_service.delete_holding(db, holding)


@router.get("/pnl", response_model=PnLSummary)
async def get_pnl(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    return await portfolio_service.get_pnl_summary(db, uuid.UUID(user_id))


@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    return await portfolio_service.list_transactions(db, uuid.UUID(user_id))


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def add_transaction(
    data: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await portfolio_service.add_transaction(db, uuid.UUID(user_id), data)
