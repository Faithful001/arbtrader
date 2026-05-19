"""Arbitrage domain - Celery tasks."""
import structlog
from src.infrastructure.celery.app import app

logger = structlog.get_logger(__name__)


@app.task(name="src.domains.arbitrage.tasks.recalculate_all_opportunities", bind=True, max_retries=3)
def recalculate_all_opportunities(self):
    """Recalculate all arbitrage opportunities - runs every N minutes via beat."""
    import asyncio
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domains.arbitrage.service import arbitrage_service

    async def _run():
        async with AsyncSessionFactory() as db:
            count = await arbitrage_service.recalculate_all(db)
            await db.commit()
            return count

    try:
        count = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("Arbitrage recalc task complete", opportunities=count)
        return {"opportunities_found": count}
    except Exception as exc:
        logger.error("Arbitrage recalc task failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
