import secrets
from datetime import UTC, datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from db.database import get_db
from db.models import Plan, User

bearer_scheme = HTTPBearer()

def _is_dev_skip_verification() -> bool:
    return str(getattr(settings, "SKIP_EMAIL_VERIFICATION", "")).lower() == "true"

# 🔧 TEST MODE: dummy password functions (no hashing)
def hash_password(password: str) -> str:
    return "dummy_hash_" + password

def verify_password(plain: str, hashed: str) -> bool:
    return hashed.startswith("dummy_hash_") and hashed == "dummy_hash_" + plain

def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    if not user.is_verified and not _is_dev_skip_verification():
        raise HTTPException(status_code=403, detail={"code": "EMAIL_NOT_VERIFIED", "message": "Подтверди email"})
    return user

async def create_user(email: str, password: str, db: AsyncSession) -> User:
    from db.models import User
    user = User(
        email=email,
        password_hash=hash_password(password),
        verification_token=secrets.token_urlsafe(32),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

async def verify_email_token(token: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный токен")
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    await db.commit()
    await db.refresh(user)
    return user
