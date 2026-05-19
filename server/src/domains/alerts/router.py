"""Alerts domain - API router."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.core.security import get_current_user_id
from src.domains.alerts.service import alert_service
from src.domains.alerts.schemas import AlertCreate, AlertUpdate, AlertResponse, AlertTriggerResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    return await alert_service.list_alerts(db, uuid.UUID(user_id))


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    data: AlertCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await alert_service.create_alert(db, uuid.UUID(user_id), data)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    data: AlertUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_service.get_alert(db, alert_id)
    if not alert or str(alert.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return await alert_service.update_alert(db, alert, data)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_service.get_alert(db, alert_id)
    if not alert or str(alert.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await alert_service.delete_alert(db, alert)


@router.get("/{alert_id}/history", response_model=List[AlertTriggerResponse])
async def get_alert_history(
    alert_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_service.get_alert(db, alert_id)
    if not alert or str(alert.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return await alert_service.list_triggers(db, alert_id)
