# CLAUDE.md — VideoDownloader Backend

## Стек
- Язык: Python 3.12
- Фреймворк: FastAPI 0.109+, SQLAlchemy 2.0 (Mapped/declarative)
- БД: SQLite (aiosqlite), PostgreSQL (готов к переключению)
- Аутентификация: JWT (python-jose), bcrypt (passlib)
- Тестирование: pytest, pytest-asyncio, httpx TestClient
- Линтинг: ruff (стиль + pyupgrade), mypy (статическая типизация)
- Инфраструктура: Docker, GitHub Actions CI/CD, Celery (заглушка)

## Архитектура
Многопользовательский API для скачивания видео с системой ролей, лимитов качества и подписок.
Модули: `auth` (регистрация, верификация, JWT), `downloads` (очередь задач, парсинг ссылок), `billing` (Stripe webhook), `worker` (Celery tasks).
Асинхронная архитектура на `asyncio` + `SQLAlchemy 2.0`.

## Правила написания кода
- Все функции — с docstrings на английском
- Комментарии к бизнес-логике — на русском
- Никаких «магических чисел» — только константы в `config.py`
- Обработка ошибок: try/except с возвратом `HTTPException`
- Модульность: один файл = одна ответственность
- Типизация: `str | None` вместо `Optional[str]`, `list[T]` вместо `List[T]`, `Mapped[...]` для SQLAlchemy

## Инструкции для ИИ (совместимость с Serena MCP)
- Держать код модульным для семантической индексации
- Чёткие имена функций и переменных на английском
- Документировать все публичные интерфейсы
- Использовать Pydantic для схем данных, SQLAlchemy 2.0 стиль для моделей
- Тесты писать через `TestClient`, моки — в `tests/conftest.py`
