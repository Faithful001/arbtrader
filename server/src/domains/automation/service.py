"""Automation domain — service (MVP stubs, execution disabled)."""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domains.automation.models import AutomationRule


class AutomationService:

    async def list_rules(self, db: AsyncSession, user_id: uuid.UUID) -> List[AutomationRule]:
        result = await db.execute(select(AutomationRule).where(AutomationRule.user_id == user_id))
        return list(result.scalars().all())

    async def create_rule(self, db: AsyncSession, user_id: uuid.UUID, data: dict) -> AutomationRule:
        rule = AutomationRule(
            user_id=user_id,
            name=data["name"],
            rule_type=data["rule_type"],
            conditions=data.get("conditions", {}),
            actions=data.get("actions", {}),
            is_active=False,  # LOCKED — no execution in MVP
            description=data.get("description"),
        )
        db.add(rule)
        await db.flush()
        return rule


automation_service = AutomationService()
