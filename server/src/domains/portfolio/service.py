"""Portfolio domain - service layer."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.domains.portfolio.models import Portfolio, Transaction
from src.domains.portfolio.schemas import PortfolioCreate, TransactionCreate, PnLSummary


class PortfolioService:

    async def add_holding(self, db: AsyncSession, user_id: uuid.UUID, data: PortfolioCreate) -> Portfolio:
        holding = Portfolio(
            user_id=user_id,
            card_id=data.card_id,
            market_id=data.market_id,
            quantity=data.quantity,
            buy_price_gbp=data.buy_price_gbp,
            buy_date=data.buy_date,
            condition=data.condition,
            notes=data.notes,
        )
        db.add(holding)
        await db.flush()
        return holding

    async def list_holdings(self, db: AsyncSession, user_id: uuid.UUID) -> List[Portfolio]:
        result = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
        return list(result.scalars().all())

    async def get_holding(self, db: AsyncSession, holding_id: uuid.UUID) -> Optional[Portfolio]:
        result = await db.execute(select(Portfolio).where(Portfolio.id == holding_id))
        return result.scalar_one_or_none()

    async def delete_holding(self, db: AsyncSession, holding: Portfolio) -> None:
        await db.delete(holding)

    async def add_transaction(self, db: AsyncSession, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            card_id=data.card_id,
            market_id=data.market_id,
            portfolio_id=data.portfolio_id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            price_gbp=data.price_gbp,
            fees_gbp=data.fees_gbp,
            transaction_date=data.transaction_date,
            notes=data.notes,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def list_transactions(self, db: AsyncSession, user_id: uuid.UUID) -> List[Transaction]:
        result = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
        return list(result.scalars().all())

    async def get_pnl_summary(self, db: AsyncSession, user_id: uuid.UUID) -> PnLSummary:
        holdings = await self.list_holdings(db, user_id)
        txs = await self.list_transactions(db, user_id)

        total_invested = sum(h.buy_price_gbp * h.quantity for h in holdings)
        current_value = sum((h.current_value_gbp or h.buy_price_gbp) * h.quantity for h in holdings)
        unrealized_pnl = current_value - total_invested

        realized_pnl = sum(
            (tx.price_gbp - tx.fees_gbp) * tx.quantity
            if tx.transaction_type == "sell" else 0
            for tx in txs
        )

        total_pnl = realized_pnl + unrealized_pnl
        roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        return PnLSummary(
            total_invested_gbp=round(total_invested, 2),
            current_value_gbp=round(current_value, 2),
            total_realized_pnl_gbp=round(realized_pnl, 2),
            total_unrealized_pnl_gbp=round(unrealized_pnl, 2),
            total_pnl_gbp=round(total_pnl, 2),
            roi_percent=round(roi, 2),
            holdings_count=len(holdings),
        )

    async def update_valuations(self, db: AsyncSession) -> int:
        """Update current_value_gbp for all holdings using latest normalized prices."""
        from src.domains.pricing.models import PriceNormalized
        from sqlalchemy import desc
        holdings = await db.execute(select(Portfolio))
        count = 0
        for holding in holdings.scalars().all():
            latest = await db.execute(
                select(PriceNormalized)
                .where(PriceNormalized.card_id == holding.card_id)
                .order_by(desc(PriceNormalized.snapshot_at))
                .limit(1)
            )
            price = latest.scalar_one_or_none()
            if price:
                holding.current_value_gbp = price.price_gbp
                count += 1
        await db.flush()
        return count


portfolio_service = PortfolioService()
