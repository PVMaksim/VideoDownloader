"""
Celery tasks — background video downloading
"""
import asyncio
import logging
import re
import shutil
from pathlib import Path

from celery import Celery
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from config import settings
from db.models import Download, DownloadStatus

log = logging.getLogger(__name__)

# Celery app
celery = Celery(
    "videograb",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    worker_prefetch_multiplier=1,   # одна задача за раз на воркер
    task_acks_late=True,            # подтверждаем только после выполнения
)

# Синхронный движок для Celery (не async)
sync_engine = create_engine(settings.DATABASE_URL_SYNC)


def get_sync_db():
    """Sync DB session for Celery"""
    with Session(sync_engine) as session:
        yield session


@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def download_video(
    self,
    task_id: str,
    video_url: str,
    cookies: str,
    referer: str,
    user_agent: str,
    height: int,
    title: str,
    user_plan: str,
):
    """
    Main Celery task — downloads video using yt-dlp.
    Updates Download record in DB with progress.
    """
    log.info(f"[{task_id}] Старт скачивания: {video_url[:60]}")

    with Session(sync_engine) as db:
        try:
            _set_status(db, task_id, DownloadStatus.DOWNLOADING, progress=0)
            filepath = _run_ytdlp(task_id, video_url, cookies, referer, user_agent, height, title, db)
            _set_status(db, task_id, DownloadStatus.READY, progress=100, filename=filepath.name)
            log.info(f"[{task_id}] Готово: {filepath.name}")

        except Exception as e:
            log.error(f"[{task_id}] Ошибка: {e}")
            _set_status(db, task_id, DownloadStatus.ERROR, error=str(e))
            # Удаляем незаконченные файлы
            shutil.rmtree(Path(settings.DOWNLOAD_DIR) / task_id, ignore_errors=True)
            raise self.retry(exc=e)


def _run_ytdlp(task_id, video_url, cookies, referer, user_agent, height, title, db) -> Path:
    """Run yt-dlp subprocess and track progress"""
    import subprocess

    out_dir = Path(settings.DOWNLOAD_DIR) / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r'[^\w\sа-яёА-ЯЁ-]', '', title or "video")[:60].strip()
    out_path = out_dir / f"{safe_title}-{height}p.%(ext)s"

    cmd = [
        "yt-dlp",
        "-f", f"best[height<={height}]/bestvideo[height<={height}]+bestaudio/best",
        "-o", str(out_path),
        "--no-playlist",
        "--newline",
        "--merge-output-format", "mp4",
        "--no-warnings",
    ]

    if cookies:
        cookies_file = out_dir / "cookies.txt"
        cookies_file.write_text(_cookies_to_netscape(cookies, referer))
        cmd += ["--cookies", str(cookies_file)]

    if referer:
        cmd += ["--referer", referer]
    if user_agent:
        cmd += ["--user-agent", user_agent]

    cmd.append(video_url)

    log.debug(f"[{task_id}] CMD: {' '.join(cmd[:8])}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        log.debug(f"[{task_id}] yt-dlp: {line}")
        progress = _parse_progress(line)
        if progress is not None:
            _set_status(db, task_id, DownloadStatus.DOWNLOADING, progress=int(progress))

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"yt-dlp завершился с кодом {process.returncode}")

    # Найти скачанный файл
    files = [f for f in out_dir.iterdir() if f.suffix in (".mp4", ".mkv", ".webm") and "cookies" not in f.name]
    if not files:
        raise RuntimeError("Файл не найден после скачивания")

    return files[0]


def _set_status(db: Session, task_id: str, status: DownloadStatus, **kwargs):
    """Update download status in DB"""
    values = {"status": status, **kwargs}
    db.execute(
        update(Download).where(Download.task_id == task_id).values(**values)
    )
    db.commit()


def _parse_progress(line: str) -> float | None:
    """Parse '[download]  47.3%' lines from yt-dlp"""
    m = re.search(r'\[download\]\s+([\d.]+)%', line)
    return float(m.group(1)) if m else None


def _cookies_to_netscape(cookies_str: str, referer: str = "") -> str:
    """Convert 'name=val; name2=val2' to Netscape cookie format"""
    from urllib.parse import urlparse
    try:
        domain = urlparse(referer).hostname or "."
    except Exception:
        domain = "."

    lines = ["# Netscape HTTP Cookie File"]
    for pair in cookies_str.split(";"):
        pair = pair.strip()
        if "=" not in pair:
            continue
        name, _, value = pair.partition("=")
        lines.append(f"{domain}\tFALSE\t/\tFALSE\t0\t{name.strip()}\t{value.strip()}")

    return "\n".join(lines)
