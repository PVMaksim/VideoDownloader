# VideoDownloader Backend

Многопользовательский API для скачивания видео с поддержкой подписок и ограничений качества.

## Быстрый старт (локально)
```bash
# 1. Копируем окружение
cp .env.example .env

# 2. Запускаем через Docker
docker-compose up --build

# Или локально (нужен Python 3.12)
pip install uv && uv pip install -r requirements.txt
uvicorn src.main:app --reload
