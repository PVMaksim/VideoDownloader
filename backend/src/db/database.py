from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

Base = declarative_base()

# Параметры создаются динамически в зависимости от типа БД
engine_kwargs = {}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True

db_url = settings.DATABASE_URL
if db_url and 'postgresql://' in db_url and '+asyncpg' not in db_url:
    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
engine = create_async_engine(db_url, **engine_kwargs)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
