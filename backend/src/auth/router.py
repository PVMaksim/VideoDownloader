"""
Auth endpoints — register, verify, login, me, resend
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from auth.email import send_verification_email, send_welcome_email
from auth.service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
    resend_verification,
    verify_email_token,
)
from db.database import get_db
from db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Схемы ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    plan: str
    is_verified: bool
    downloads_today: int = 0

class ResendRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str


# ── Роуты ────────────────────────────────────────────────────────

@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(
    req: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Register new user, send verification email"""
    user = await create_user(req.email, req.password, db)

    # Отправляем письмо в фоне — не блокируем ответ
    background_tasks.add_task(
        send_verification_email, user.email  , user.verification_token )  # type: ignore[arg-type]  

    return MessageResponse(
        message=f"Аккаунт создан. Проверь почту {req.email} — отправили письмо с подтверждением."
    )


@router.get("/verify", response_model=MessageResponse)
async def verify_email(
    token: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Verify email by token from link"""
    user = await verify_email_token(token, db)

    # Welcome письмо только при первой верификации
    background_tasks.add_task(send_welcome_email, user.email or "")  # type: ignore[arg-type]

    return MessageResponse(message="Email подтверждён! Теперь можешь войти.")


@router.post("/resend", response_model=MessageResponse)
async def resend(
    req: ResendRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email"""
    user = await resend_verification(req.email, db)

    if user:
        background_tasks.add_task(
            send_verification_email, user.email  , user.verification_token )  # type: ignore[arg-type]  

    # Всегда отвечаем одинаково — не раскрываем существование аккаунта
    return MessageResponse(
        message="Если аккаунт существует — письмо отправлено повторно."
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and return JWT token"""
    user = await authenticate_user(req.email, req.password, db)
    return TokenResponse(access_token=create_access_token(user.id )  )


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user info"""
    from downloads.service import count_downloads_today
    today = await count_downloads_today(current_user.id ,   db)  
    return UserResponse(
        id=current_user.id ,   email=current_user.email  ,
        plan=current_user.plan,
        is_verified=current_user.is_verified,
        downloads_today=today,
    )  # type: ignore[union-attr]
