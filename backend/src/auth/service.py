"""
Authentication service — JWT, passwords, email verification
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.database import get_db
from db.models import User, Plan

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ── Пароли ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ──────────────────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """Create JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def decode_token(token: str) -> Optional[int]:
    """Decode JWT, return user_id or None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


# ── Dependency: текущий пользователь ─────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency — returns authenticated user"""
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Подтверди email. Проверь почту или запроси новое письмо.",
            }
        )
    return user


# ── Регистрация ───────────────────────────────────────────────────

async def create_user(email: str, password: str, db: AsyncSession) -> User:
    """Register new unverified user"""
    result = await db.execute(select(User).where(User.email == email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email уже зарегистрирован")

    token = secrets.token_urlsafe(32)   # случайный токен верификации
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        plan=Plan.FREE,
        is_verified=False,
        verification_token=token,
    )
    db.add(user)
    await db.flush()
    return user


# ── Верификация email ─────────────────────────────────────────────

async def verify_email_token(token: str, db: AsyncSession) -> User:
    """Verify email by token, activate user"""
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Неверный или истёкший токен")

    if user.is_verified:
        return user  # уже верифицирован — просто возвращаем

    user.is_verified = True
    user.verification_token = None  # инвалидируем токен после использования
    return user


async def resend_verification(email: str, db: AsyncSession) -> User:
    """Generate new verification token and resend email"""
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        # Не раскрываем существует ли пользователь
        return None

    if user.is_verified:
        return None

    user.verification_token = secrets.token_urlsafe(32)
    return user


# ── Логин ─────────────────────────────────────────────────────────

async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    """Verify credentials. Email must be verified to get token."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Подтверди email перед входом. Проверь почту.",
            }
        )
    return user
