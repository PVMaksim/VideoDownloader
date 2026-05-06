"""Download endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.service import get_current_user
from db.database import get_db
from db.models import User
from downloads.service import (
    create_download_record,
    get_download,
    get_file_path,
    get_user_download_stats,
    get_user_downloads,
)

router = APIRouter(prefix="/api", tags=["downloads"])

class DownloadRequest(BaseModel):
    video_url: str
    cookies: str | None = None
    referer: str | None = None
    user_agent: str | None = None
    height: int | None = 1080
    title: str | None = "video"

class DownloadResponse(BaseModel):
    task_id: str
    status: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    filename: str | None
    error: str | None
    platform: str | None

class HistoryItem(BaseModel):
    task_id: str
    status: str
    title: str | None
    platform: str | None
    height: int | None
    created_at: str

    class Config:
        from_attributes = True

@router.post("/download", response_model=DownloadResponse, status_code=201)
async def create_download(
    req: DownloadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
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
    except ValueError as e:
        # Преобразуем бизнес-ошибки в HTTP 402 с кодом
        error_msg = str(e)
        code = "QUALITY_LOCKED" if "720p" in error_msg else "LIMIT_REACHED"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": code, "message": error_msg}
        )
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
