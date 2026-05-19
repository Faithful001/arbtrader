"""Automation domain - API router (MVP: read + create only, no execution)."""
import uuid
from typing import List, Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.core.security import get_current_user_id
from src.domains.automation.service import automation_service

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/rules")
async def list_rules(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    rules = await automation_service.list_rules(db, uuid.UUID(user_id))
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "rule_type": r.rule_type,
            "conditions": r.conditions,
            "actions": r.actions,
            "is_active": r.is_active,
            "description": r.description,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]


@router.post("/rules", status_code=201)
async def create_rule(
    data: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    rule = await automation_service.create_rule(db, uuid.UUID(user_id), data)
    return {
        "id": str(rule.id),
        "name": rule.name,
        "is_active": False,
        "note": "Automation execution is disabled in MVP. Rules can be defined but not executed.",
    }
