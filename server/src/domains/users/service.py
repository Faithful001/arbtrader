"""Users domain — service layer."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domains.users.models import User
from src.domains.users.schemas import UserCreate, UserUpdate
from src.core.security import hash_password, verify_password, create_access_token


class UserService:

    async def create_user(self, db: AsyncSession, data: UserCreate) -> User:
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            preferences={
                "min_profit_gbp": 5.0,
                "min_confidence": 0.6,
                "notify_telegram": True,
                "notify_email": False,
                "currency_display": "GBP",
            },
        )
        db.add(user)
        await db.flush()
        return user

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[str]:
        """Authenticate and return a JWT token, or None if invalid."""
        user = await self.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return create_access_token(str(user.id))

    async def update_user(self, db: AsyncSession, user: User, data: UserUpdate) -> User:
        if data.telegram_chat_id is not None:
            user.telegram_chat_id = data.telegram_chat_id
        if data.preferences is not None:
            user.preferences = {**user.preferences, **data.preferences}
        await db.flush()
        return user


user_service = UserService()
