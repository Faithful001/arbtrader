"""Pricing domain - Celery tasks."""
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


@app.task(name="src.domains.pricing.tasks.cleanup_stale_pricing_data", bind=True, max_retries=3)
def cleanup_stale_pricing_data(self):
    """Clean up old pricing records based on retention policy."""
    import asyncio
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domains.pricing.service import pricing_service
    from src.core.config import settings

    async def _run():
        async with AsyncSessionFactory() as db:
            count = await pricing_service.cleanup_stale_data(db, settings.PRICING_DATA_RETENTION_DAYS)
            await db.commit()
            return count

    try:
        count = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("Pricing data cleanup complete", deleted_records=count, days_retained=settings.PRICING_DATA_RETENTION_DAYS)
        return {"deleted_records": count}
    except Exception as exc:
        logger.error("Pricing data cleanup failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)
