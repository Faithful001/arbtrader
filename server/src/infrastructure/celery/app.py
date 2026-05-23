from celery import Celery

from src.core.config import settings

app = Celery(
    "arbtrader",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.domains.pricing.tasks",
        "src.domains.arbitrage.tasks",
        "src.domains.alerts.tasks",
        "src.domains.portfolio.tasks",
        "src.domains.users.tasks",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    
    # Reduce Redis connections
    worker_gossip=False,        # disables node discovery (saves 1-2 connections)
    worker_heartbeat=None,      # disables heartbeat (saves 1 connection)
    broker_pool_limit=1,        # limit broker connection pool to 1
    redis_max_connections=3,    # hard cap on Redis connections
)

# Import beat schedule after app is configured
from src.infrastructure.celery.beat_schedule import BEAT_SCHEDULE
app.conf.beat_schedule = BEAT_SCHEDULE
