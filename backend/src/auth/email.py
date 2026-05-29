# UNIQUE_MARKER_EMAIL_2026
import sys, logging, traceback, resend
from config import settings

sys.stderr.write("🚀 [MARKER] EMAIL LOADED\n")
sys.stderr.flush()

log = logging.getLogger(__name__)
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

async def send_verification_email(email: str, token: str):
    try:
        sys.stderr.write(f"🚀 [EMAIL] sending to {email}\n")
        sys.stderr.flush()
        
        if getattr(settings, 'DISABLE_EMAIL_SENDING', False):
            sys.stderr.write(f"⚠️ [EMAIL] sending disabled\n")
            sys.stderr.flush()
            return
        
        verify_url = f"{settings.APP_URL}/auth/verify?token={token}"
        html = f"<html><body><a href='{verify_url}'>Подтвердить</a></body></html>"
        
        sys.stderr.write(f"🚀 [EMAIL] calling resend API\n")
        sys.stderr.flush()
        
        response = resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Подтверди email — VideoGrab",
            "html": html,
        })
        
        sys.stderr.write(f"🚀 [EMAIL] sent: {response}\n")
        sys.stderr.flush()
        
    except Exception as e:
        sys.stderr.write(f"❌ [EMAIL] EXCEPTION: {type(e).__name__}: {e}\n")
        sys.stderr.flush()
        sys.stderr.write(f"❌ [EMAIL] TRACEBACK:\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        raise
