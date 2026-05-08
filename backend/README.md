# VideoDownloader Backend

Многопользовательский API для скачивания видео с поддержкой подписок и ограничений качества. Поддерживает регистрацию, верификацию по email, очередь задач на скачивание и интеграцию со Stripe.

## Быстрый старт (локально)

```bash
# 1. Копируем окружение
cp .env.example .env

# 2. Запускаем через Docker
docker-compose up --build

# Или локально (нужен Python 3.12)
pip install uv && uv pip install -r requirements.txt
uvicorn src.main:app --reload
Деплой на VPS
Автоматически через GitHub Actions при пуше в main.
Вручную:
ssh user@vps "cd /opt/videograb && docker compose pull && docker compose up -d"Переменные окружения
Необходимые переменные:
DATABASE_URL: строка подключения к БД (sqlite+aiosqlite:///./videograb.db)
JWT_SECRET: секретный ключ для токенов
SKIP_EMAIL_VERIFICATION: true для локальной разработки
Структура проекта
src/: исходный код (auth, downloads, billing, worker)
tests/: интеграционные тесты
.github/workflows/: CI/CD пайплайны
Dockerfile: образ для API
Dockerfile.worker: образ для Celery worker (с ffmpeg)
Тестирование
pytest tests/ -v
