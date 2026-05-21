"""Portfolio domain - service layer."""
import uuid
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domains.portfolio.models import Portfolio, Transaction
from src.domains.portfolio.schemas import (
    PortfolioCreate, TransactionCreate, PnLSummary, PnLHistoryPoint,
)


class PortfolioService:

    async def add_holding(self, db: AsyncSession, user_id: uuid.UUID, data: PortfolioCreate) -> Portfolio:
        from src.domains.pricing.models import PriceNormalized
        from sqlalchemy import desc

        # Query the latest normalized price for this card to set as current market value
        latest_price_stmt = (
            select(PriceNormalized)
            .where(PriceNormalized.card_id == data.card_id)
            .order_by(desc(PriceNormalized.snapshot_at))
            .limit(1)
        )
        latest_price = (await db.execute(latest_price_stmt)).scalar_one_or_none()
        initial_val = latest_price.price_gbp if latest_price else data.buy_price_gbp

        holding = Portfolio(
            user_id=user_id,
            card_id=data.card_id,
            market_id=data.market_id,
            quantity=data.quantity,
            buy_price_gbp=data.buy_price_gbp,
            buy_date=data.buy_date,
            condition=data.condition,
            notes=data.notes,
            current_value_gbp=initial_val,
        )
        db.add(holding)
        await db.flush()
        return holding

    async def list_holdings(self, db: AsyncSession, user_id: uuid.UUID) -> List[dict]:
        """Return holdings enriched with card_name and market_name via joins."""
        from src.domains.cards.models import Card
        from src.domains.markets.models import Market

        stmt = (
            select(Portfolio, Card, Market)
            .join(Card, Card.id == Portfolio.card_id)
            .join(Market, Market.id == Portfolio.market_id)
            .where(Portfolio.user_id == user_id)
        )
        rows = (await db.execute(stmt)).all()
        result = []
        for holding, card, market in rows:
            d = {
                "id": holding.id,
                "user_id": holding.user_id,
                "card_id": holding.card_id,
                "market_id": holding.market_id,
                "quantity": holding.quantity,
                "buy_price_gbp": holding.buy_price_gbp,
                "buy_date": holding.buy_date,
                "current_value_gbp": holding.current_value_gbp,
                "condition": holding.condition,
                "notes": holding.notes,
                "created_at": holding.created_at,
                "card_name": card.name,
                "card_image_url": card.image_url,
                "unrealized_pnl_gbp": round(
                    ((holding.current_value_gbp or holding.buy_price_gbp) - holding.buy_price_gbp)
                    * holding.quantity, 2
                ),
                "unrealized_pnl_percent": round(
                    (((holding.current_value_gbp or holding.buy_price_gbp) - holding.buy_price_gbp)
                     / holding.buy_price_gbp * 100) if holding.buy_price_gbp else 0, 2
                ),
                "market": market.name,
            }
            result.append(d)
        return result

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

        total_invested = sum(h["buy_price_gbp"] * h["quantity"] for h in holdings)
        current_value = sum(
            (h["current_value_gbp"] or h["buy_price_gbp"]) * h["quantity"] for h in holdings
        )
        unrealized_pnl = current_value - total_invested

        realized_pnl = sum(
            (tx.price_gbp - tx.fees_gbp) * tx.quantity
            if tx.transaction_type == "sell" else 0
            for tx in txs
        )

        total_pnl = realized_pnl + unrealized_pnl
        roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
        history = await self.get_pnl_history(db, user_id)

        return PnLSummary(
            total_invested_gbp=round(total_invested, 2),
            current_value_gbp=round(current_value, 2),
            total_realized_pnl_gbp=round(realized_pnl, 2),
            total_unrealized_pnl_gbp=round(unrealized_pnl, 2),
            total_pnl_gbp=round(total_pnl, 2),
            roi_percent=round(roi, 2),
            holdings_count=len(holdings),
            history=history,
        )

    async def get_pnl_history(
        self, db: AsyncSession, user_id: uuid.UUID, days: int = 30
    ) -> list:
        """Return daily portfolio value for the last `days` days."""
        from src.domains.pricing.models import PriceNormalized

        holdings = await self.list_holdings(db, user_id)
        if not holdings:
            return []

        card_ids = [h["card_id"] for h in holdings]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(PriceNormalized)
            .where(
                PriceNormalized.card_id.in_(card_ids),
                PriceNormalized.snapshot_at >= cutoff,
            )
            .order_by(PriceNormalized.snapshot_at)
        )
        prices = result.scalars().all()

        # Group latest price per card per day
        daily_prices: dict = defaultdict(dict)
        for p in prices:
            date_str = p.snapshot_at.strftime("%Y-%m-%d")
            daily_prices[date_str][str(p.card_id)] = p.price_gbp

        # Walk days in order, carrying forward last known price per card
        all_dates = sorted(daily_prices.keys())
        last_known: dict = {}
        history = []
        for date_str in all_dates:
            last_known.update(daily_prices[date_str])
            total = sum(
                last_known.get(str(h["card_id"]), h["buy_price_gbp"]) * h["quantity"]
                for h in holdings
            )
            history.append(PnLHistoryPoint(date=date_str, value=round(total, 2)))

        return history

    async def update_valuations(self, db: AsyncSession) -> int:
        """Update current_value_gbp for all holdings using latest normalized prices."""
        from src.domains.pricing.models import PriceNormalized
        from sqlalchemy import desc
        holdings_result = await db.execute(select(Portfolio))
        count = 0
        for holding in holdings_result.scalars().all():
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
