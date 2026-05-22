"""Users domain - service layer."""
import structlog
from src.infrastructure.redis.client import redis_client
import uuid
import random
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from redis.asyncio import Redis

from src.core.config import settings
from src.domains.users.tasks import send_otp
from src.domains.users.models import User
from src.domains.users.schemas import UserCreate, UserUpdate
from src.core.security import hash_password, verify_password, create_access_token


logger = structlog.get_logger(__name__)


class UserService:

    async def create_user(self, db: AsyncSession, data: UserCreate) -> User:
        user = User(
            email=data.email,
            password_hash="no_password_otp_auth",
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

    async def request_otp(self, db: AsyncSession, email: str) -> str:
        user = await self.get_by_email(db, email)
        if not user:
            # Create user if doesn't exist
            from src.domains.users.schemas import UserCreate
            user = await self.create_user(db, UserCreate(email=email))

        # Generate 6 digit OTP
        otp = str(random.randint(100000, 999999))
        
        send_otp.delay(email, otp)

        logger.info("Task queued", email=email)
        
        # Store in Redis
        await redis_client.setex(f"otp:{email}", 300, otp)  # 5 minutes expiry
        # await redis_client.aclose()
        
        # Log to console for development
        print("="*40)
        print(f" OTP for {email}: {otp} ")
        print("="*40)
        
        return otp

    async def verify_otp(self, db: AsyncSession, email: str, otp: str) -> Optional[str]:
        stored_otp = await redis_client.get(f"otp:{email}")
        
        if not stored_otp or stored_otp != otp:
            # await redis_client.aclose()
            return None
            
        # Clear the OTP
        await redis_client.delete(f"otp:{email}")
        # await redis_client.aclose()
        
        user = await self.get_by_email(db, email)
        if not user:
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
