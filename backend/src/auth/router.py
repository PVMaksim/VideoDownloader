# UNIQUE_MARKER_ROUTER_2026
import sys, logging, traceback
from fastapi import APIRouter, Depends, HTTPException, status
from db.models import User
from auth.service import create_user, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from config import settings

sys.stderr.write("🚀 [MARKER] ROUTER LOADED\n")
sys.stderr.flush()

from auth.email import send_verification_email
from auth.service import create_user, get_current_user
from db.database import get_db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class MessageResponse(BaseModel):
    message: str

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(req.email, req.password, db)
        
        # ✅ Проверяем, нужно ли отправлять email
        if not settings.SKIP_EMAIL_VERIFICATION:
            await send_verification_email(user.email, user.verification_token)
        
        return MessageResponse(message=f"✅ Аккаунт создан для {req.email}")
        
    except Exception as e:
        log.error(f"Ошибка регистрации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from fastapi import HTTPException
from auth.service import authenticate_user, create_access_token

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(req.email, req.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email не подтверждён")
    return TokenResponse(access_token=create_access_token(user.id))

from datetime import UTC, datetime, timedelta
import secrets
from sqlalchemy import select
from db.models import User
from auth.service import hash_password

class ResetRequest(BaseModel):
    email: EmailStr

class NewPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(req: ResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if user:
        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        print(f"🔑 [DEV] Reset token for {req.email}: {user.reset_token}")
    return MessageResponse(message="Если аккаунт существует, инструкция отправлена на email.")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(req: NewPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.reset_token == req.token))
    user = result.scalar_one_or_none()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()
    return MessageResponse(message="Пароль успешно изменён.")

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить данные текущего пользователя"""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "plan": str(current_user.plan) if current_user.plan else "free",
    }
