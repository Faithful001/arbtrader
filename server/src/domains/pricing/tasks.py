"""Pricing domain — Celery tasks."""
import structlog
from src.infrastructure.celery.app import app

logger = structlog.get_logger(__name__)


@app.task(name="src.domains.pricing.tasks.ingest_ebay_prices", bind=True, max_retries=3)
def ingest_ebay_prices(self, region: str):
    """Ingest sold prices from eBay for a region."""
    import asyncio
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domains.pricing.service import pricing_service

    async def _run():
        async with AsyncSessionFactory() as db:
            count = await pricing_service.ingest_for_region(db, region)
            await db.commit()
            return count

    try:
        count = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("Price ingestion task complete", region=region, records=count)
        return {"region": region, "records_ingested": count}
    except Exception as exc:
        logger.error("Price ingestion task failed", region=region, error=str(exc))
        raise self.retry(exc=exc, countdown=120)
