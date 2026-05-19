"""
Celery Beat schedule - defines periodic task intervals.
All intervals are configurable via settings.
"""
from celery.schedules import crontab

from src.core.config import settings

BEAT_SCHEDULE = {
    # Price ingestion: every N minutes (default 120)
    "ingest-ebay-uk-prices": {
        "task": "src.domains.pricing.tasks.ingest_ebay_prices",
        "schedule": settings.PRICE_INGESTION_INTERVAL_MINUTES * 60,
        "args": ["UK"],
        "options": {"queue": "ingestion"},
    },
    "ingest-ebay-us-prices": {
        "task": "src.domains.pricing.tasks.ingest_ebay_prices",
        "schedule": settings.PRICE_INGESTION_INTERVAL_MINUTES * 60,
        "args": ["US"],
        "options": {"queue": "ingestion"},
    },
    # Arbitrage recalculation: every N minutes (default 60)
    "recalculate-arbitrage": {
        "task": "src.domains.arbitrage.tasks.recalculate_all_opportunities",
        "schedule": settings.ARBITRAGE_RECALC_INTERVAL_MINUTES * 60,
        "options": {"queue": "arbitrage"},
    },
    # Alert dispatch: every 5 minutes
    "dispatch-alerts": {
        "task": "src.domains.alerts.tasks.dispatch_pending_alerts",
        "schedule": 300,
        "options": {"queue": "alerts"},
    },
    # Portfolio valuation: every 6 hours
    "update-portfolio-valuations": {
        "task": "src.domains.portfolio.tasks.update_all_portfolio_valuations",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "portfolio"},
    },
    # Database cleanup: every day at midnight
    "cleanup-stale-pricing-data": {
        "task": "src.domains.pricing.tasks.cleanup_stale_pricing_data",
        "schedule": crontab(minute=0, hour=0),
        "options": {"queue": "ingestion"},
    },
}
