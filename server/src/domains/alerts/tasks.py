"""Alerts domain - Celery tasks (event-driven alert dispatch)."""
import structlog
from src.infrastructure.celery.app import app

logger = structlog.get_logger(__name__)


@app.task(name="src.domains.alerts.tasks.dispatch_pending_alerts", bind=True, max_retries=3)
def dispatch_pending_alerts(self):
    """Check active opportunities against alert rules and dispatch via Telegram."""
    import asyncio
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domains.alerts.service import alert_service
    from src.domains.arbitrage.service import arbitrage_service
    from src.domains.users.service import user_service
    from src.infrastructure.external_apis.telegram.bot import telegram_bot

    async def _run():
        dispatched = 0
        async with AsyncSessionFactory() as db:
            alerts = await alert_service.get_active_alerts(db)
            if not alerts:
                return 0

            opportunities, _ = await arbitrage_service.get_opportunities_feed(db, limit=50)

            for alert in alerts:
                user = await user_service.get_by_id(db, alert.user_id)
                if not user or not user.telegram_chat_id:
                    continue

                conditions = alert.conditions
                min_profit = conditions.get("min_profit_gbp", 5.0)
                min_roi = conditions.get("min_roi_percent", 0.0)

                for opp in opportunities:
                    if alert.trigger_type == "new_opportunity":
                        if opp.net_profit_gbp >= min_profit and opp.roi_percent >= min_roi:
                            ok = await telegram_bot.send_opportunity_alert(
                                chat_id=user.telegram_chat_id,
                                card_name=str(opp.card_id),
                                buy_market=str(opp.buy_market_id),
                                sell_market=str(opp.sell_market_id),
                                net_profit_gbp=opp.net_profit_gbp,
                                roi_percent=opp.roi_percent,
                                confidence=opp.confidence_score,
                            )
                            await alert_service.record_trigger(
                                db, alert.id,
                                payload={"opportunity_id": str(opp.id)},
                                delivered=ok,
                            )
                            dispatched += 1
            await db.commit()
        return dispatched

    try:
        count = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("Alert dispatch complete", dispatched=count)
        return {"dispatched": count}
    except Exception as exc:
        logger.error("Alert dispatch failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
