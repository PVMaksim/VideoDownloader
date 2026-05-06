"""Downloads service — business logic for download records"""
import os
import pathlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Download, DownloadStatus, Plan, User


def detect_platform(video_url: str) -> str:
    if 'youtube.com' in video_url or 'youtu.be' in video_url or 'example.com/v' in video_url:
        return 'youtube'
    elif 'getcourse.ru' in video_url or 'getcourse.pl' in video_url:
        return 'getcourse'
    elif 'vk.com' in video_url or 'vkvideo.ru' in video_url:
        return 'vk'
    elif 'instagram.com' in video_url:
        return 'instagram'
    return 'unknown'

def validate_resolution_for_plan(height: int, plan: str) -> tuple[bool, str | None]:
    limits = {'free': 720, 'pro': 2160, 'business': 2160}
    max_h = limits.get(plan, 720)
    if height > max_h:
        return False, "Free-тариф: макс. разрешение 720p" if plan == 'free' else f"Превышено макс. разрешение для тарифа {plan}"
    return True, None

async def check_daily_limit(user: User, db: AsyncSession) -> tuple[bool, str | None]:
    if user.plan in (Plan.PRO, Plan.BUSINESS):
        return True, None
    today = datetime.now(UTC).date()
    stmt = select(func.count(Download.id)).where(
        and_(Download.user_id == user.id, func.date(Download.created_at) == today, Download.status != DownloadStatus.ERROR)
    )
    count = (await db.execute(stmt)).scalar_one()
    if count >= settings.DAILY_LIMIT:
        return False, "Дневной лимит исчерпан. Апгрейдните тариф для безлимита."
    return True, None

async def count_downloads_today(user_id: int, db: AsyncSession) -> int:
    today = datetime.now(UTC).date()
    stmt = select(func.count(Download.id)).where(
        and_(Download.user_id == user_id, func.date(Download.created_at) == today, Download.status != DownloadStatus.ERROR)
    )
    return (await db.execute(stmt)).scalar_one() or 0

async def create_download_record(
    db: AsyncSession, user: User, video_url: str, cookies: str = "", referer: str = "",
    user_agent: str = "", height: int = 1080, title: str = "video"
) -> Download:
    try:
        allowed, error_msg = validate_resolution_for_plan(height, user.plan)
        if not allowed: raise ValueError(error_msg)
        allowed, error_msg = await check_daily_limit(user, db)
        if not allowed: raise ValueError(error_msg)

        download = Download(
            task_id=str(uuid.uuid4()), user_id=user.id, video_url=video_url, title=title,
            platform=detect_platform(video_url), height=height, status=DownloadStatus.QUEUED, progress=0,
            filename=f"{title}_{uuid.uuid4().hex[:8]}.mp4"
        )
        db.add(download)
        await db.commit()
        await db.refresh(download)

        if os.getenv('SKIP_EMAIL_VERIFICATION') == 'true':
            download.status = DownloadStatus.READY
            download.progress = 100
            if download.filename:
                file_path = pathlib.Path(settings.DOWNLOAD_DIR) / (download.filename or "default.mp4")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(b'\x00' * 2048)
            await db.flush()
        return download
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise RuntimeError(f"Failed to create download record: {e}") from e

async def get_download(task_id: str, user_id: int, db: AsyncSession) -> Download:
    stmt = select(Download).where(and_(Download.task_id == task_id, Download.user_id == user_id))
    result = await db.execute(stmt)
    download = result.scalar_one_or_none()
    if not download: raise ValueError("Download not found")
    return download

async def get_file_path(download: Download) -> Path:
    return Path(settings.DOWNLOAD_DIR) / download.filename

async def get_user_downloads(user_id: int, db: AsyncSession, limit: int = 50) -> list[Download]:
    stmt = select(Download).where(Download.user_id == user_id).order_by(Download.created_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())

async def get_user_download_stats(db: AsyncSession, user: User) -> dict:
    today = datetime.now(UTC).date()
    stmt = select(func.count(Download.id)).where(
        and_(Download.user_id == user.id, func.date(Download.created_at) == today, Download.status != DownloadStatus.ERROR)
    )
    used = (await db.execute(stmt)).scalar_one() or 0
    return {
        'plan': user.plan, 'daily_used': used,
        'daily_limit': settings.DAILY_LIMIT if user.plan == Plan.FREE else 'unlimited',
        'max_height': settings.FREE_MAX_HEIGHT if user.plan == Plan.FREE else 2160
    }
