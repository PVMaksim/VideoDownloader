"""Downloads router — HTTP endpoints for video downloads"""
import pathlib
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.service import get_current_user
from db.database import get_db
from db.models import Download, DownloadStatus, Plan, User
from schemas.downloads import DownloadRequest, DownloadResponse, HistoryItem, StatusResponse
from worker.tasks import download_video
from fastapi import HTTPException

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
            cookies=getattr(req, "cookies", None) or "",
            referer=getattr(req, "referer", None) or "",
            user_agent=getattr(req, "user_agent", None) or "",
            height=getattr(req, "height", None) or 1080,
            title=getattr(req, "title", None) or "video",
            db=db,
        )
    except ValueError as e:
        # Бизнес-ошибки → HTTP 402
        error_msg = str(e)
        code = "QUALITY_LOCKED" if "720p" in error_msg else "LIMIT_REACHED"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": code, "message": error_msg}
        )

    # 2. 🚀 Отправляем задачу в Celery
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

    # 3. Возвращаем ответ
    return DownloadResponse(
        task_id=download.task_id,
        status=download.status,
        video_url=download.video_url,
        height=download.height
    )


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    download = await get_download(task_id, current_user.id, db)
    download_url = None
    if download.status == DownloadStatus.READY:
        download_url = f"/api/downloads/file/{download.task_id}"
    return StatusResponse(
        task_id=download.task_id,
        status=download.status,
        progress=download.progress or 0,
        filename=download.filename,
        error=download.error_message,
        platform=download.platform,
        download_url=download_url,
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
            filename=d.filename,
            status=d.status,
            video_url=d.video_url,
            created_at=d.created_at,
        )
        for d in downloads
    ]


@router.get("/stats", summary="Статистика скачиваний пользователя")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_download_stats(db, current_user)


@router.post("/sizes")
async def get_video_sizes(
    req: dict,
    current_user: User = Depends(get_current_user),
):
    """Получить размеры видео для доступных качеств"""
    import yt_dlp
    import asyncio

    video_url = req.get("video_url")
    if not video_url:
        raise HTTPException(status_code=400, detail="video_url required")

    # Запускаем yt-dlp в потоке (blocking operation)
    def get_formats():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info
        except Exception as e:
            print(f"Error extracting info: {e}")
            return None

    # Выполняем в отдельном потоке
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_formats)

    if not info:
        return {"sizes": {}}

    # Группируем форматы по высоте и находим максимальный размер
    sizes = {}
    qualities = [360, 480, 720, 1080, 1440, 2160]

    for height in qualities:
        # Ищем все форматы с этой высотой
        formats = info.get('formats', [])
        relevant_formats = [
            f for f in formats
            if f.get('height') == height and f.get('filesize')
        ]

        if relevant_formats:
            # Берём максимальный размер (лучшее качество для этой высоты)
            max_size = max(f['filesize'] for f in relevant_formats)
            sizes[height] = max_size

    return {"sizes": sizes}

@router.delete("/file/{task_id}")
async def delete_file(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить скачанный файл с сервера и запись из БД"""
    import os
    from pathlib import Path

    # 1. Ищем запись в БД
    stmt = select(Download).where(
        Download.task_id == task_id,
        Download.user_id == current_user.id
    )
    result = await db.execute(stmt)
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # 2. Удаляем файл с диска (если существует)
    file_deleted = False
    if download.filename:
        # Пробуем несколько возможных путей
        possible_paths = [
            Path(settings.DOWNLOAD_DIR) / download.filename,
            Path("/app/downloads") / download.filename,
            Path("/tmp/videodownloader") / download.filename,
        ]

        for file_path in possible_paths:
            if file_path.exists():
                try:
                    os.remove(file_path)
                    file_deleted = True
                    print(f"[CLEANUP] Файл удалён: {file_path}")
                    break
                except Exception as e:
                    print(f"[CLEANUP] Ошибка удаления {file_path}: {e}")

    # 3. Удаляем запись из БД
    await db.delete(download)
    await db.commit()

    print(f"[CLEANUP] Запись {task_id} удалена из БД, файл удалён: {file_deleted}")

    return {
        "deleted": file_deleted,
        "task_id": task_id,
        "db_record_removed": True
    }