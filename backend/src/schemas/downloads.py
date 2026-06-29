from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DownloadRequest(BaseModel):
    video_url: str
    height: int | None = None
    cookies: Optional[str] = None
    referer: Optional[str] = None
    user_agent: Optional[str] = None
    format: Optional[str] = "best"
    filename_hint: Optional[str] = None

class DownloadResponse(BaseModel):
    task_id: str
    status: str = "queued"
    message: str = "Task created"

class HistoryItem(BaseModel):
    task_id: str
    filename: str | None = None
    status: str
    created_at: datetime
    video_url: str | None = None

class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    eta_seconds: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
