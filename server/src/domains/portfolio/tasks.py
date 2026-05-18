"""Portfolio domain — Celery tasks."""
import structlog
from src.infrastructure.celery.app import app

logger = structlog.get_logger(__name__)


@app.task(name="src.domains.portfolio.tasks.update_all_portfolio_valuations", bind=True, max_retries=3)
def update_all_portfolio_valuations(self):
    """Update portfolio current values from latest price snapshots."""
    import asyncio
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domains.portfolio.service import portfolio_service

    async def _run():
        async with AsyncSessionFactory() as db:
            count = await portfolio_service.update_valuations(db)
            await db.commit()
            return count

    try:
        count = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("Portfolio valuation update complete", updated=count)
        return {"holdings_updated": count}
    except Exception as exc:
        logger.error("Portfolio valuation update failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)
