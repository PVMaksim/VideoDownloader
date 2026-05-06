import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

os.environ["SKIP_EMAIL_VERIFICATION"] = "true"
os.environ["DISABLE_EMAIL_SENDING"] = "true"
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_stub")

test_db = tempfile.mktemp(suffix="_test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from db.database import Base, get_db  # noqa: E402

engine = create_async_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
AsyncTestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = AsyncTestSession()
    yield session
    await session.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
def client(db_session):
    async def override_get_db():
        yield db_session
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def _cleanup():
    yield
    p = Path(test_db)
    if p.exists():
        p.unlink()
