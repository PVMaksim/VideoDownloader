"""
Download service — создание задач, проверка лимитов, статусы
"""
import uuid
from datetime import datetime, timezone, date
from pathlib import Path
import logging

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Download, DownloadStatus, User, Plan

log = logging.getLogger(__name__)


# ── Лимиты ───────────────────────────────────────────────────────

async def count_downloads_today(user_id: int, db: AsyncSession) -> int:
    """Count successful/active downloads today"""
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = await db.execute(
        select(func.count(Download.id)).where(
            and_(
                Download.user_id == user_id,
                Download.created_at >= today_start,
                Download.status.in_([
                    DownloadStatus.QUEUED,
                    DownloadStatus.DOWNLOADING,
                    DownloadStatus.READY,
                ])
            )
        )
    )
    return result.scalar() or 0


async def check_limits(user: User, height: int, db: AsyncSession):
    """Check if user can create new download. Raises HTTPException if not."""

    if user.plan == Plan.FREE:
        # Проверяем дневной лимит
        today_count = await count_downloads_today(user.id, db)
        if today_count >= settings.FREE_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "LIMIT_REACHED",
                    "message": f"Дневной лимит ({settings.FREE_DAILY_LIMIT} скачивания) исчерпан. Перейди на Pro.",
                    "limit": settings.FREE_DAILY_LIMIT,
                    "used": today_count,
                }
            )

        # Проверяем максимальное качество
        if height and height > settings.FREE_MAX_HEIGHT:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "QUALITY_LOCKED",
                    "message": f"Качество выше {settings.FREE_MAX_HEIGHT}p доступно только на Pro.",
                    "max_height": settings.FREE_MAX_HEIGHT,
                }
            )


# ── Создание задачи ───────────────────────────────────────────────

async def create_download_task(
    user: User,
    video_url: str,
    cookies: str,
    referer: str,
    user_agent: str,
    height: int,
    title: str,
    db: AsyncSession,
) -> Download:
    """Create download task in DB and enqueue to Celery"""

    await check_limits(user, height, db)

    task_id = str(uuid.uuid4())
    download = Download(
        user_id=user.id,
        task_id=task_id,
        status=DownloadStatus.QUEUED,
        video_url=video_url,
        title=title,
        height=height,
        platform=detect_platform(video_url),
    )
    db.add(download)
    await db.flush()

    # Ставим задачу в Celery очередь
    from worker.tasks import download_video
    download_video.delay(
        task_id=task_id,
        video_url=video_url,
        cookies=cookies,
        referer=referer,
        user_agent=user_agent,
        height=height,
        title=title,
        user_plan=user.plan,
    )

    log.info(f"[{task_id}] Задача создана для user={user.id} url={video_url[:60]}")
    return download


# ── Получение статуса ─────────────────────────────────────────────

async def get_download(task_id: str, user_id: int, db: AsyncSession) -> Download:
    """Get download task, verify ownership"""
    result = await db.execute(
        select(Download).where(
            and_(Download.task_id == task_id, Download.user_id == user_id)
        )
    )
    download = result.scalar_one_or_none()
    if not download:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return download


async def get_file_path(download: Download) -> Path:
    """Return path to downloaded file"""
    if download.status != DownloadStatus.READY:
        raise HTTPException(status_code=425, detail="Файл ещё не готов")

    path = Path(settings.DOWNLOAD_DIR) / download.task_id / download.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return path


# ── История ───────────────────────────────────────────────────────

async def get_user_downloads(user_id: int, db: AsyncSession, limit: int = 20):
    """Get recent downloads for user"""
    result = await db.execute(
        select(Download)
        .where(Download.user_id == user_id)
        .order_by(Download.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ── Утилиты ───────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    if "gceuproxy.com" in url: return "getcourse"
    if "kinescope" in url: return "kinescope"
    if "youtube.com" in url or "youtu.be" in url: return "youtube"
    if "vk.com" in url or "vkvideo.ru" in url: return "vk"
    if "instagram.com" in url: return "instagram"
    return "other"
