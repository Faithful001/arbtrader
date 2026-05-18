"""Alerts domain — service layer."""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domains.alerts.models import Alert, AlertTrigger
from src.domains.alerts.schemas import AlertCreate, AlertUpdate


class AlertService:

    async def create_alert(self, db: AsyncSession, user_id: uuid.UUID, data: AlertCreate) -> Alert:
        alert = Alert(
            user_id=user_id,
            name=data.name,
            trigger_type=data.trigger_type,
            conditions=data.conditions,
            delivery_channel=data.delivery_channel,
        )
        db.add(alert)
        await db.flush()
        return alert

    async def list_alerts(self, db: AsyncSession, user_id: uuid.UUID) -> List[Alert]:
        result = await db.execute(select(Alert).where(Alert.user_id == user_id))
        return list(result.scalars().all())

    async def get_alert(self, db: AsyncSession, alert_id: uuid.UUID) -> Optional[Alert]:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def update_alert(self, db: AsyncSession, alert: Alert, data: AlertUpdate) -> Alert:
        if data.name is not None:
            alert.name = data.name
        if data.conditions is not None:
            alert.conditions = data.conditions
        if data.is_active is not None:
            alert.is_active = data.is_active
        await db.flush()
        return alert

    async def delete_alert(self, db: AsyncSession, alert: Alert) -> None:
        await db.delete(alert)

    async def get_active_alerts(self, db: AsyncSession) -> List[Alert]:
        result = await db.execute(select(Alert).where(Alert.is_active == True))
        return list(result.scalars().all())

    async def record_trigger(
        self, db: AsyncSession, alert_id: uuid.UUID, payload: dict,
        opportunity_id: Optional[uuid.UUID] = None, delivered: bool = False,
        error: Optional[str] = None,
    ) -> AlertTrigger:
        trigger = AlertTrigger(
            alert_id=alert_id,
            opportunity_id=opportunity_id,
            payload=payload,
            delivered=delivered,
            delivery_error=error,
        )
        db.add(trigger)
        await db.flush()
        return trigger

    async def list_triggers(self, db: AsyncSession, alert_id: uuid.UUID) -> List[AlertTrigger]:
        result = await db.execute(
            select(AlertTrigger).where(AlertTrigger.alert_id == alert_id)
        )
        return list(result.scalars().all())


alert_service = AlertService()
