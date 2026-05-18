"""Downloads router — HTTP endpoints for video downloads"""
import pathlib
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from src.database import get_db
from src.models import Download, DownloadStatus, Plan, User
from schemas.downloads import DownloadRequest, DownloadResponse, HistoryItem, StatusResponse
from worker.tasks import download_video  # ✅ ИМПОРТ ЗАДАЧИ

from .service import (
    check_daily_limit,
    create_download_record,
    detect_platform,
    get_download,
    get_file_path,
    get_user_download_stats,
    get_user_downloads,
    validate_resolution_for_plan,
)

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("", response_model=DownloadResponse, status_code=status.HTTP_201_CREATED)
async def create_download(
    req: DownloadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создаёт запись о скачивании и отправляет задачу в Celery"""
    try:
        # 1. Создаём запись в БД
        download = await create_download_record(
            user=current_user,
            video_url=req.video_url,
            cookies=req.cookies or "",
            referer=req.referer or "",
            user_agent=req.user_agent or "",
            height=req.height or 1080,
            title=req.title or "video",
            db=db,
        )
        
        # 2. 🚀 ОТПРАВЛЯЕМ ЗАДАЧУ В CELERY
        download_video.apply_async(
            args=[
                download.task_id,
                download.video_url,
                download.cookies or "",
                download.referer or "",
                download.user_agent or "",
                download.height or 1080,
                download.title or "video",
                current_user.plan.value if hasattr(current_user, "plan") else "free",
            ],
            queue="celery"
        )
        
    except ValueError as e:
        # Бизнес-ошибки → HTTP 402
        error_msg = str(e)
        code = "QUALITY_LOCKED" if "720p" in error_msg else "LIMIT_REACHED"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": code, "message": error_msg}
        )
    
    # 3. Возвращаем ответ (снаружи try/except)
    return DownloadResponse(task_id=download.task_id, status=download.status)


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    download = await get_download(task_id, current_user.id, db)
    return StatusResponse(
        task_id=download.task_id,
        status=download.status,
        progress=download.progress or 0,
        filename=download.filename,
        error=download.error_message,
        platform=download.platform,
    )


@router.get("/file/{task_id}")
async def download_file(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    download = await get_download(task_id, current_user.id, db)
    path = await get_file_path(download)
    return FileResponse(
        path=str(path),
        filename=download.filename,
        media_type="video/mp4",
    )


@router.get("/history", response_model=list[HistoryItem])
async def history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    downloads = await get_user_downloads(current_user.id, db)
    return [
        HistoryItem(
            task_id=d.task_id,
            status=d.status,
            title=d.title,
            platform=d.platform,
            height=d.height,
            created_at=d.created_at.isoformat(),
        )
        for d in downloads
    ]


@router.get("/stats", summary="Статистика скачиваний пользователя")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_download_stats(db, current_user)
