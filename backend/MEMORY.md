# MEMORY.md — VideoDownloader Backend

## Последняя сессия: 2026-05-08
### Сделано
- Настроен GitHub Actions CI/CD (lint, test, docker build).
- Исправлен Dockerfile: разделение на API и Worker (ffmpeg только в worker).
- Добавлен `[project]` в `pyproject.toml` для корректной сборки зависимостей.
- Фиксы типов в `auth/router.py` и `downloads/service.py` (mypy, union-attr).
- Успешный запуск тестов (7 passed) и линтеров (ruff, mypy).
- Файлы контекста перемещены в корень репозитория.

### Проблемы / Баги
- [ ] Предупреждение FastAPI `@app.on_event` (deprecated) — отложено, проигнорировано в pytest.
- [ ] Celery Worker не подключен к реальному брокеру (Redis).

### Принятые решения
- Использовать `pyproject.toml` для зависимостей, но генерировать `requirements.txt` для Docker.
- Моки для тестов в `conftest.py`.
- Строгая типизация без `# type: ignore`, где возможно.

## Следующая сессия
- [ ] Настройка реального Celery брокера (Redis).
- [ ] Подключение реального видеопарсера в Worker.
- [ ] Деплой на VPS.

## Известный технический долг
- `src/worker/tasks.py`: заглушка, требует реализации.
- Миграция на `lifespan` в FastAPI.
