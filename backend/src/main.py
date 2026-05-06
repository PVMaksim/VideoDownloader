"""VideoGrab Backend v2 — Multi-user API with email verification"""
import asyncio
import logging
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.router import router as auth_router
from billing.router import router as billing_router
from config import settings
from db.database import engine
from db.models import Base
from downloads.router import router as downloads_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="VideoGrab API",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(downloads_router)
app.include_router(billing_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.now(UTC).isoformat()}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Path(settings.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    asyncio.create_task(_cleanup_loop())
    log.info("VideoGrab Backend v2 запущен ✅")


async def _cleanup_loop():
    """Delete downloaded files older than FILE_TTL_HOURS"""
    while True:
        await asyncio.sleep(1800)
        ttl = settings.FILE_TTL_HOURS * 3600
        base = Path(settings.DOWNLOAD_DIR)
        if not base.exists():
            continue
        for d in base.iterdir():
            if d.is_dir() and time.time() - d.stat().st_mtime > ttl:
                shutil.rmtree(d, ignore_errors=True)
                log.info(f"Очищена папка: {d.name}")
