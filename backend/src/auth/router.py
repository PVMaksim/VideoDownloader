# UNIQUE_MARKER_ROUTER_2026
import sys, logging, traceback
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

sys.stderr.write("🚀 [MARKER] ROUTER LOADED\n")
sys.stderr.flush()

from auth.email import send_verification_email
from auth.service import create_user
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
        sys.stderr.write(f"🚀 [ROUTER] register called for {req.email}\n")
        sys.stderr.flush()
        
        user = await create_user(req.email, req.password, db)
        sys.stderr.write(f"🚀 [ROUTER] user created: {user.email}\n")
        sys.stderr.flush()
        
        sys.stderr.write(f"🚀 [ROUTER] calling send_verification_email\n")
        sys.stderr.flush()
        
        await send_verification_email(user.email, user.verification_token)
        
        sys.stderr.write(f"🚀 [ROUTER] email sent, returning response\n")
        sys.stderr.flush()
        
        return MessageResponse(message=f"✅ DEBUG_2026: Аккаунт создан для {req.email}")
        
    except Exception as e:
        sys.stderr.write(f"❌ [ROUTER] EXCEPTION: {type(e).__name__}: {e}\n")
        sys.stderr.flush()
        sys.stderr.write(f"❌ [ROUTER] TRACEBACK:\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        raise
