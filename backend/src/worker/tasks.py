"""
Celery tasks — background video downloading
"""
from config import settings
import logging
import re
import shutil
from pathlib import Path

from celery import Celery
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from celery_config import app
from db.models import Download, DownloadStatus

log = logging.getLogger(__name__)

# Celery app
celery = Celery(
    "videodownloader",
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
            _set_status(db, task_id, DownloadStatus.ERROR, error_message=str(e))
            # Удаляем незаконченные файлы
            shutil.rmtree(Path(settings.DOWNLOAD_DIR) / task_id, ignore_errors=True)
            raise self.retry(exc=e)

def _run_ytdlp(task_id, video_url, cookies, referer, user_agent, height, title, db) -> Path:
    """Run yt-dlp subprocess and track progress"""
    
    log.info(f"[{task_id}] Полученные параметры: title={title}, height={height}")
    
    # Если title не передан или пустой - получаем через yt-dlp
    if not title or title == "video":
        try:
            log.info(f"[{task_id}] Получаем название видео через yt-dlp...")
            info_cmd = [
                "yt-dlp", 
                "--get-title", 
                "--no-warnings",
                "--no-playlist",
                video_url
            ]
            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                title = result.stdout.strip()
                log.info(f"[{task_id}] Получено название: {title}")
            else:
                log.warning(f"[{task_id}] Не удалось получить название: {result.stderr}")
        except Exception as e:
            log.warning(f"[{task_id}] Ошибка при получении названия: {e}")
    
    import subprocess

    out_dir = Path(settings.DOWNLOAD_DIR) / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Получаем правильное название видео через yt-dlp
    try:
        info_cmd = ["yt-dlp", "--get-title", "--no-warnings", video_url]
        if cookies:
            cookies_file = out_dir / "cookies.txt"
            cookies_file.write_text(_cookies_to_netscape(cookies, referer))
            info_cmd += ["--cookies", str(cookies_file)]
        
        result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            title = result.stdout.strip()
    except Exception as e:
        log.warning(f"[{task_id}] Не удалось получить название: {e}")
        title = title or "video"

    # Очищаем название от недопустимых символов для файловой системы
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title or "video")[:100].strip()
    # Убираем "- YouTube" из конца, если есть
    safe_title = re.sub(r'\s*-\s*YouTube\s*$', '', safe_title)
    # Убираем лишние пробелы
    safe_title = ' '.join(safe_title.split())
    # убирает "(1924) " в начале
    safe_title = re.sub(r'^\(\d+\)\s*', '', safe_title)  
    
    log.info(f"[{task_id}] Название файла: {safe_title}")
    
    out_path = out_dir / f"{safe_title}.%(ext)s"

    cmd = [
        "yt-dlp",
        "-f", f"bestvideo[height<={height}][vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "-o", str(out_path),
        "--no-playlist",
        "--newline",
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--remote-components", "ejs:github",
        "--ffmpeg-location", "/usr/bin/ffmpeg",
        "--recode-video", "mp4",
    ]

    if cookies:
        cookies_file = out_dir / "cookies.txt"
        if not cookies_file.exists():
            cookies_file.write_text(_cookies_to_netscape(cookies, referer))
        cmd += ["--cookies", str(cookies_file)]

    if referer:
        cmd += ["--referer", referer]
    if user_agent:
        cmd += ["--user-agent", user_agent]

    cmd.append(video_url)

    log.info(f"[{task_id}] Команда: {' '.join(cmd[:8])}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Читаем stdout для прогресса
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        log.debug(f"[{task_id}] yt-dlp: {line}")
        progress = _parse_progress(line)
        if progress is not None:
            _set_status(db, task_id, DownloadStatus.DOWNLOADING, progress=int(progress))

    process.wait()
    
    # Проверяем stderr на ошибки
    stderr_output = process.stderr.read()
    if process.returncode != 0:
        log.error(f"[{task_id}] yt-dlp stderr: {stderr_output}")
        raise RuntimeError(f"yt-dlp завершился с кодом {process.returncode}")

    # Найти скачанный файл
    files = [f for f in out_dir.iterdir() if f.suffix in (".mp4", ".mkv", ".webm") and "cookies" not in f.name]
    if not files:
        raise RuntimeError("Файл не найден после скачивания")
    
    file_path = files[0]
    
    # Проверка размера файла
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise RuntimeError("Файл пустой")
    if file_size < 1024 * 100:  # меньше 100KB
        log.warning(f"[{task_id}] Файл очень маленький: {file_size} байт")
    
    log.info(f"[{task_id}] Файл сохранён: {file_path.name} ({file_size} байт)")

    return file_path

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
    
    # Пустые cookies
    if not cookies_str:
        return "# Netscape HTTP Cookie File\n"
    
    domain = ".youtube.com"
    try:
        if referer:
            parsed = urlparse(referer)
            domain = "." + parsed.netloc.split(".")[-2] + "." + parsed.netloc.split(".")[-1]
    except:
        pass
    
    lines = ["# Netscape HTTP Cookie File"]
    cookies = cookies_str.split(";")
    
    for cookie in cookies:
        if "=" not in cookie:
            continue
        name, value = cookie.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or not value:
            continue
        # Format: domain flag path secure expiration name value
        lines.append(f"{domain}\tTRUE\t/\tFALSE\t9999999999\t{name}\t{value}")
    
    return "\n".join(lines) + "\n"
