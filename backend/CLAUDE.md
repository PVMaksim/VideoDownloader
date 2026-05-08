# CLAUDE.md — VideoDownloader Backend

## Стек
- Язык: Python 3.12
- Фреймворк: FastAPI 0.109+, SQLAlchemy 2.0 (Mapped/declarative)
- БД: SQLite (aiosqlite) + PostgreSQL (готов к переключению)
- Аутентификация: JWT (python-jose), bcrypt (passlib)
- Тестирование: pytest, pytest-asyncio, httpx TestClient
- Линтинг: ruff (стиль + pyupgrade), mypy (статическая типизация)
- Инфраструктура: Docker, GitHub Actions CI/CD

## Архитектура
Многопользовательский API для скачивания видео с ограничением качества и квот по тарифам. Поддерживает регистрацию, верификацию по email, очередь задач на скачивание, Stripe-биллинг.

## Структура проекта
- src/main.py — точка входа FastAPI, CORS, подключение роутеров
- src/config.py — Pydantic Settings, переменные окружения
- src/db/ — SQLAlchemy 2.0 модели (User, Download), async engine
- src/auth/ — регистрация, логин, верификация, JWT-токены
- src/downloads/ — создание задач, проверка лимитов, детекция платформ
- src/billing/ — Stripe webhook, управление подписками
- src/worker/ — Celery tasks (заглушка, готово к подключению)

## Правила написания кода
- Все функции — с docstrings на английском
- Комментарии к бизнес-логике — на русском
- Никаких «магических чисел» — только константы в config.py
- Обработка ошибок: try/except с конкретными исключениями
- Модульность: один файл = одна ответственность
- Типизация: str | None вместо Optional[str], list[T] вместо List[T]

## Инструкции для ИИ
- Держать код модульным для семантической индексации
- Чёткие имена функций и переменных на английском
- Документировать все публичные интерфейсы
- Тесты писать через TestClient, моки — в tests/conftest.py

## Запуск и тесты
# Локально: uvicorn src.main:app --reload
# Тесты: pytest tests/ -v
# Линтеры: ruff check src/ tests/ --fix && mypy src/
