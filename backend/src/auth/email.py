"""
Email service — sends verification emails via Resend API
resend.com — 3000 бесплатных писем в месяц, простая интеграция
"""
import logging

import resend

from config import settings

log = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


async def send_verification_email(email: str, token: str):
    """Send email verification link to new user"""
    verify_url = f"{settings.APP_URL}/auth/verify?token={token}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 40px auto; color: #111;">
      <div style="background: #6366f1; border-radius: 10px; padding: 32px; text-align: center; margin-bottom: 24px;">
        <h1 style="color: white; margin: 0; font-size: 24px;">▶ VideoGrab</h1>
      </div>

      <h2 style="font-size: 20px; margin-bottom: 8px;">Подтверди email</h2>
      <p style="color: #555; line-height: 1.6; margin-bottom: 24px;">
        Нажми на кнопку ниже чтобы активировать аккаунт VideoGrab.
        Ссылка действительна 24 часа.
      </p>

      <a href="{verify_url}"
         style="display: inline-block; background: #6366f1; color: white;
                padding: 12px 28px; border-radius: 8px; text-decoration: none;
                font-weight: 600; font-size: 15px;">
        Подтвердить email
      </a>

      <p style="color: #999; font-size: 12px; margin-top: 32px;">
        Если ты не регистрировался — просто проигнорируй это письмо.<br>
        <a href="{verify_url}" style="color: #6366f1;">{verify_url}</a>
      </p>
    </body>
    </html>
    """

    # Skip sending in test/dev mode
    if getattr(settings, 'SKIP_EMAIL_VERIFICATION', False) or getattr(settings, 'DISABLE_EMAIL_SENDING', False):
        log.info(f'Email sending disabled, skipping: {email}')
        return
    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Подтверди email — VideoGrab",
            "html": html,
        })
        log.info(f"Письмо верификации отправлено: {email}")
    except Exception as e:
        log.error(f"Ошибка отправки письма на {email}: {e}")
        raise


async def send_welcome_email(email: str):
    """Send welcome email after successful verification"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 40px auto; color: #111;">
      <div style="background: #6366f1; border-radius: 10px; padding: 32px; text-align: center; margin-bottom: 24px;">
        <h1 style="color: white; margin: 0; font-size: 24px;">▶ VideoGrab</h1>
      </div>

      <h2 style="font-size: 20px; margin-bottom: 8px;">Добро пожаловать! 🎉</h2>
      <p style="color: #555; line-height: 1.6;">
        Аккаунт активирован. Ты на бесплатном тарифе:
      </p>

      <div style="background: #f4f4f8; border-radius: 8px; padding: 16px; margin: 20px 0;">
        <p style="margin: 4px 0; color: #333;">✅ <b>3 скачивания</b> в день</p>
        <p style="margin: 4px 0; color: #333;">✅ Качество до <b>720p</b></p>
        <p style="margin: 4px 0; color: #333;">✅ GetCourse, YouTube, VK, Instagram</p>
      </div>

      <p style="color: #555;">
        Установи расширение для Chrome и начни пользоваться.
      </p>

      <a href="{settings.APP_URL}"
         style="display: inline-block; background: #22c55e; color: white;
                padding: 12px 28px; border-radius: 8px; text-decoration: none;
                font-weight: 600; font-size: 15px;">
        Открыть VideoGrab
      </a>
    </body>
    </html>
    """

    # Skip sending in test/dev mode
    if getattr(settings, 'SKIP_EMAIL_VERIFICATION', False) or getattr(settings, 'DISABLE_EMAIL_SENDING', False):
        log.info(f'Email sending disabled, skipping: {email}')
        return
    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [email],
            "subject": "Добро пожаловать в VideoGrab!",
            "html": html,
        })
    except Exception as e:
        log.warning(f"Не удалось отправить welcome email на {email}: {e}")
        # Не критично — не поднимаем ошибку
