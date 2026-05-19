"""Users domain - API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.core.security import get_current_user_id
from src.domains.users.service import user_service
from src.domains.users.schemas import UserCreate, UserUpdate, UserResponse, TokenResponse, OTPRequest, OTPVerify

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/auth/request-otp", status_code=200)
async def request_otp(data: OTPRequest, db: AsyncSession = Depends(get_db)):
    await user_service.request_otp(db, data.email)
    return {"message": "OTP generated and logged to console"}


@router.post("/auth/verify-otp", response_model=TokenResponse)
async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(get_db)):
    token = await user_service.verify_otp(db, data.email, data.otp)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    user = await user_service.get_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    user = await user_service.get_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_service.update_user(db, user, data)
