"""Общий конфиг Celery для API и Worker"""
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "videodownloader",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.worker.tasks"]
)

# Надёжные настройки для Docker
app.conf.update(
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)
