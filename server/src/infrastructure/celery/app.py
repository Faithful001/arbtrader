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
)

# Import beat schedule after app is configured
from src.infrastructure.celery.beat_schedule import BEAT_SCHEDULE  # noqa: E402
app.conf.beat_schedule = BEAT_SCHEDULE
