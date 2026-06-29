from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_URL: str = "https://neoxis.store"
    SKIP_EMAIL_VERIFICATION: bool = False
    SKIP_QUOTA_CHECK: bool = False
    DISABLE_EMAIL_SENDING: bool = False
    CELERY_BROKER_URL: str = "redis://redis:6379/0"

    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    DATABASE_URL_SYNC: str = "postgresql+psycopg2://user:pass@db:5432/videodownloader"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "VideoGrab"
    DEBUG: bool = False
    API_V1_STR: str = "/api"

    DATABASE_URL: str = "postgresql+asyncpg://videodownloader:K71K71mP92xL24a@db:5432/videodownloader"

    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    RESEND_API_KEY: str = "re_V7JJUFNr_E3WEiLbzShhqvbCWJ4Ve6C23"
    FROM_EMAIL: str = "noreply@videodownloader.app"
    EMAIL_FROM: str = "VideoGrab <onboarding@resend.dev>"

    DOWNLOAD_DIR: str = "/app/storage"
    FILE_TTL_HOURS: int = 24
    MAX_FILE_SIZE_MB: int = 2048

    FREE_MAX_HEIGHT: int = 720
    DAILY_LIMIT: int = 3

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""


    # Password reset
    FRONTEND_URL: str = "https://neoxis.store"
    
    # SMTP settings (optional)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = 587
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    SMTP_FROM: str = "noreply@videodownloader.app"

    SKIP_AUTH: bool = False
settings = Settings()
