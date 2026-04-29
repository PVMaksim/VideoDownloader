from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "VideoGrab"
    DEBUG: bool = False
    APP_URL: str = "https://yourdomain.com"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://videograb:password@db:5432/videograb"
    DATABASE_URL_SYNC: str = "postgresql://videograb:password@db:5432/videograb"

    # Redis + Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 дней
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24
    ALGORITHM: str = "HS256"

    # Email — Resend (resend.com, есть бесплатный план 3000 писем/мес)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "VideoGrab <noreply@yourdomain.com>"

    # Downloads
    DOWNLOAD_DIR: str = "/tmp/videograb"
    FILE_TTL_HOURS: int = 2

    # Plans
    FREE_DAILY_LIMIT: int = 3
    FREE_MAX_HEIGHT: int = 720
    PRO_MAX_HEIGHT: int = 1080   # зарезервировано на будущее

    class Config:
        env_file = ".env"


settings = Settings()
