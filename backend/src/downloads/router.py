"""
Download endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from auth.service import get_current_user
from downloads.service import (
    create_download_task, get_download,
    get_file_path, get_user_downloads
)

router = APIRouter(prefix="/api", tags=["downloads"])


# ── Схемы ────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    video_url: str
    cookies: Optional[str] = None
    referer: Optional[str] = None
    user_agent: Optional[str] = None
    height: Optional[int] = 1080
    title: Optional[str] = "video"


class DownloadResponse(BaseModel):
    task_id: str
    status: str


class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    filename: Optional[str]
    error: Optional[str]
    platform: Optional[str]


class HistoryItem(BaseModel):
    task_id: str
    status: str
    title: Optional[str]
    platform: Optional[str]
    height: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


# ── Роуты ────────────────────────────────────────────────────────

@router.post("/download", response_model=DownloadResponse, status_code=201)
async def create_download(
    req: DownloadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create download task (checks plan limits)"""
    download = await create_download_task(
        user=current_user,
        video_url=req.video_url,
        cookies=req.cookies or "",
        referer=req.referer or "",
        user_agent=req.user_agent or "",
        height=req.height or 1080,
        title=req.title or "video",
        db=db,
    )
    return DownloadResponse(task_id=download.task_id, status=download.status)


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get download task status"""
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
    """Download ready file"""
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
    """Get download history"""
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
