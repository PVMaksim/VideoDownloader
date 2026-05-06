## Стек
- Язык: Python 3.12
- Фреймворк: FastAPI 0.109+
- БД: SQLite (aiosqlite) + SQLAlchemy 2.0 (Mapped/declarative)
- Аутентификация: JWT (python-jose), bcrypt (passlib)
- Тестирование: pytest, pytest-asyncio, httpx TestClient
- Линтинг: ruff (стиль + pyupgrade), mypy (статическая типизация)
- Инфраструктура: готов к Docker, GitHub Actions

## Архитектура
Многопользовательский API для скачивания видео с ограничением качества/квот по тарифам.
src/
├── main.py # Точка входа, CORS, роутеры
├── config.py # Pydantic Settings, переменные окружения
├── db/
│ ├── database.py # Async engine, sessionmaker, Base
│ └── models.py # SQLAlchemy 2.0 модели: User, Download
├── auth/
│ ├── router.py # /api/auth: register, login, verify, me
│ ├── service.py # JWT, password hashing, email-логика
│ └── email.py # Resend.com интеграция (опционально)
├── downloads/
│ ├── router.py # /api: download, status, file, history
│ └── service.py # Бизнес-логика: лимиты, детекция платформы
├── billing/
│ ├── router.py # /billing: Stripe webhook, subscription
│ └── stripe_service.py # Stripe API обёртка
└── worker/
└── tasks.py # Celery tasks (заглушка, готово к подключению)
## Правила написания кода
- Все функции — с docstrings на английском
- Комментарии к бизнес-логике — на русском
- Никаких «магических чисел» — только константы в `config.py`
- Обработка ошибок: try/except с конкретными исключениями
- Модульность: один файл = одна ответственность
- Типизация: `str | None` вместо `Optional[str]`, `list[T]` вместо `List[T]`

## Инструкции для ИИ (совместимость с Serena MCP)
- Держать код модульным для семантической индексации
- Чёткие имена функций/переменных на английском
- Документировать все публичные интерфейсы
- При изменении моделей — обновлять миграции (если будут)
- Тесты писать через `TestClient`, моки — в `tests/conftest.py`

## Запуск и тесты
```bash
# Локально
uvicorn src.main:app --reload

# Тесты
pytest tests/ -v

# Линтеры
ruff check src/ tests/ --fix
mypy src/