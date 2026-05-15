from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_URL: str = "http://localhost:8010"
    SKIP_EMAIL_VERIFICATION: bool = False
    DISABLE_EMAIL_SENDING: bool = False
    CELERY_BROKER_URL: str = "redis://redis:6379/0"

    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    DATABASE_URL_SYNC: str = "sqlite:///./videograb.db"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "VideoGrab"
    DEBUG: bool = False
    API_V1_STR: str = "/api"

    DATABASE_URL: str = "postgresql+asyncpg://videograb:K71K71mP92xL24a@db:5432/videograb"

    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@videograb.app"
    EMAIL_FROM: str = "noreply@videograb.app"

    DOWNLOAD_DIR: str = "/app/storage"
    FILE_TTL_HOURS: int = 24
    MAX_FILE_SIZE_MB: int = 2048

    FREE_MAX_HEIGHT: int = 720
    DAILY_LIMIT: int = 3

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""

settings = Settings()
